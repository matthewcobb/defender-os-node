import { ref, computed, onMounted, onBeforeUnmount, shallowRef } from 'vue';
import { DongleConfig, CommandMapping, findDevice, requestDevice } from 'node-carplay/web';
import { CarPlayWorker } from '../../../workers/types';
import { useCarplayAudio } from './useCarplayAudio';
import { useCarplayTouch } from './useCarplayTouch';
import { InitEvent } from '../../../workers/render/RenderEvents';

// Import workers using Vite's worker syntax
import RenderWorker from '../../../workers/render/Render.worker.ts?worker';
import CarPlayWorkerModule from '../../../workers/carplay/CarPlay.worker.ts?worker';

export function useCarplay(width: number, height: number) {
  const isPlugged = ref(false);
  const deviceFound = ref<boolean | null>(null);
  const retryTimeoutRef = ref<NodeJS.Timeout | null>(null);
  const canvasRef = shallowRef<HTMLCanvasElement | null>(null);
  const canvasElement = shallowRef<HTMLCanvasElement | null>(null);

  const videoChannel = new MessageChannel();
  const micChannel = new MessageChannel();

  const config: Partial<DongleConfig> = {
    width,
    height,
    fps: 60,
    mediaDelay: 300,
  };

  // Create render worker when canvas is available
  let renderWorker: Worker | null = null;

  // Create carplay worker
  const carplayWorker = new CarPlayWorkerModule() as CarPlayWorker;
  const payload = {
    videoPort: videoChannel.port1,
    microphonePort: micChannel.port1,
  };
  carplayWorker.postMessage({ type: 'initialise', payload }, [
    videoChannel.port1,
    micChannel.port1,
  ]);

  const { processAudio, getAudioPlayer, startRecording, stopRecording } = useCarplayAudio(carplayWorker, micChannel.port2);
  const sendTouchEvent = useCarplayTouch(carplayWorker, width, height);

  const clearRetryTimeout = () => {
    if (retryTimeoutRef.value) {
      clearTimeout(retryTimeoutRef.value);
      retryTimeoutRef.value = null;
    }
  };

  const checkDevice = async (request: boolean = false) => {
    const device = request ? await requestDevice() : await findDevice();
    if (device) {
      deviceFound.value = true;
      carplayWorker.postMessage({ type: 'start', payload: { config } });
    } else {
      deviceFound.value = false;
    }
  };

  // Initialize render worker when canvas is available
  function initRenderWorker() {
    if (!canvasElement.value || renderWorker) return;

    renderWorker = new RenderWorker();
    const canvas = canvasElement.value.transferControlToOffscreen();

    // Use the InitEvent class to create the correct message format
    renderWorker.postMessage(new InitEvent(canvas, videoChannel.port2), [
      canvas,
      videoChannel.port2,
    ]);
  }

  // Watch for canvas reference changes
  function setCanvas(el: HTMLCanvasElement) {
    canvasRef.value = el;
    canvasElement.value = el;
    initRenderWorker();
  }

  // Setup worker message handler
  function setupWorkerMessageHandler() {
    carplayWorker.onmessage = ((ev: MessageEvent) => {
      const { type } = ev.data;
      switch (type) {
        case 'plugged':
          isPlugged.value = true;
          break;
        case 'unplugged':
          isPlugged.value = false;
          break;
        case 'requestBuffer':
          clearRetryTimeout();
          getAudioPlayer(ev.data.message);
          break;
        case 'audio':
          clearRetryTimeout();
          processAudio(ev.data.message);
          break;
        case 'command':
          const { message: { value } } = ev.data;
          switch (value) {
            case CommandMapping.startRecordAudio:
              startRecording();
              break;
            case CommandMapping.stopRecordAudio:
              stopRecording();
              break;
          }
          break;
        case 'failure':
          if (!retryTimeoutRef.value) {
            console.error('Carplay initialization failed -- Reloading page in 30s');
            retryTimeoutRef.value = setTimeout(() => {
              window.location.reload();
            }, 30000);
          }
          break;
      }
    }) as any;
  }

  // Setup USB event handlers
  function setupUsbHandlers() {
    navigator.usb.onconnect = async () => {
      checkDevice();
    };

    navigator.usb.ondisconnect = async () => {
      const device = await findDevice();
      if (!device) {
        carplayWorker.postMessage({ type: 'stop' });
        deviceFound.value = false;
      }
    };
  }

  // Lifecycle hooks
  onMounted(() => {
    setupWorkerMessageHandler();
    setupUsbHandlers();
    checkDevice();
  });

  onBeforeUnmount(() => {
    // Cleanup
    clearRetryTimeout();
    renderWorker?.terminate();
    carplayWorker.postMessage({ type: 'stop' });
  });

  const isLoading = computed(() => !isPlugged.value);

  return {
    isPlugged,
    deviceFound,
    isLoading,
    checkDevice,
    sendTouchEvent,
    setCanvas
  };
}