import React, { createContext, useContext, useCallback, useMemo, useState, useRef, useEffect, useLayoutEffect } from 'react';
import { DongleConfig, CommandMapping, findDevice, requestDevice } from 'node-carplay/web';
import { CarPlayWorker } from '../../../workers/types';
import { useCarplayAudio } from '../hooks/useCarplayAudio';
import { useCarplayTouch } from '../hooks/useCarplayTouch';
import { InitEvent } from '../../../workers/render/RenderEvents';

// Import workers using Vite's worker syntax
import RenderWorker from '../../../workers/render/Render.worker.ts?worker';
import CarPlayWorkerModule from '../../../workers/carplay/CarPlay.worker.ts?worker';

interface CarPlayContextType {
  isPlugged: boolean;
  deviceFound: boolean | null;
  isLoading: boolean;
  checkDevice: (request?: boolean) => Promise<void>;
  sendTouchEvent: (event: PointerEvent) => void;
  canvasRef: React.RefObject<HTMLCanvasElement>;
}

const CarPlayContext = createContext<CarPlayContextType | undefined>(undefined);

export const useCarPlay = () => {
  const context = useContext(CarPlayContext);
  if (!context) {
    throw new Error('useCarPlay must be used within a CarPlayProvider');
  }
  return context;
};

interface CarPlayProviderProps {
  children: React.ReactNode;
  width: number;
  height: number;
}

export const CarPlayProvider: React.FC<CarPlayProviderProps> = ({ children, width, height }) => {
  const [isPlugged, setPlugged] = useState(false);
  const [deviceFound, setDeviceFound] = useState<boolean | null>(null);
  const retryTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [canvasElement, setCanvasElement] = useState<HTMLCanvasElement | null>(null);

  const videoChannel = useMemo(() => new MessageChannel(), []);
  const micChannel = useMemo(() => new MessageChannel(), []);

  const config: Partial<DongleConfig> = useMemo(() => ({
    width,
    height,
    fps: 60,
    mediaDelay: 300,
  }), [width, height]);

  const renderWorker = useMemo(() => {
    if (!canvasElement) return null;
    // Use the imported worker constructor directly
    const worker = new RenderWorker();
    const canvas = canvasElement.transferControlToOffscreen();
    worker.postMessage(new InitEvent(canvas, videoChannel.port2), [
      canvas,
      videoChannel.port2,
    ]);
    return worker;
  }, [canvasElement, videoChannel.port2]);

  const carplayWorker = useMemo(() => {
    // Use the imported worker constructor directly
    const worker = new CarPlayWorkerModule() as CarPlayWorker;
    const payload = {
      videoPort: videoChannel.port1,
      microphonePort: micChannel.port1,
    };
    worker.postMessage({ type: 'initialise', payload }, [
      videoChannel.port1,
      micChannel.port1,
    ]);
    return worker;
  }, [videoChannel.port1, micChannel.port1]);

  useLayoutEffect(() => {
    if (canvasRef.current) {
      setCanvasElement(canvasRef.current);
    }
  }, []);

  const { processAudio, getAudioPlayer, startRecording, stopRecording } = useCarplayAudio(carplayWorker, micChannel.port2);
  const sendTouchEvent = useCarplayTouch(carplayWorker, width, height);

  const clearRetryTimeout = useCallback(() => {
    if (retryTimeoutRef.current) {
      clearTimeout(retryTimeoutRef.current);
      retryTimeoutRef.current = null;
    }
  }, []);

  const checkDevice = useCallback(async (request: boolean = false) => {
    const device = request ? await requestDevice() : await findDevice();
    if (device) {
      setDeviceFound(true);
      const payload = { config };
      carplayWorker.postMessage({ type: 'start', payload });
    } else {
      setDeviceFound(false);
    }
  }, [carplayWorker, config]);

  // Subscribe to worker messages
  useEffect(() => {
    carplayWorker.onmessage = (ev: MessageEvent) => {
      const { type } = ev.data;
      switch (type) {
        case 'plugged':
          setPlugged(true);
          break;
        case 'unplugged':
          setPlugged(false);
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
          if (retryTimeoutRef.current == null) {
            console.error('Carplay initialization failed -- Reloading page in 30s');
            retryTimeoutRef.current = setTimeout(() => {
              window.location.reload();
            }, 30000);
          }
          break;
      }
    };
  }, [carplayWorker, clearRetryTimeout, getAudioPlayer, processAudio, startRecording, stopRecording]);

  // USB connect/disconnect handling
  useEffect(() => {
    navigator.usb.onconnect = async () => {
      checkDevice();
    };

    navigator.usb.ondisconnect = async () => {
      const device = await findDevice();
      if (!device) {
        carplayWorker.postMessage({ type: 'stop' });
        setDeviceFound(false);
      }
    };

    checkDevice();
  }, [carplayWorker, checkDevice]);

  const value = {
    isPlugged,
    deviceFound,
    isLoading: !isPlugged,
    checkDevice,
    sendTouchEvent,
    canvasRef,
  };

  return (
    <CarPlayContext.Provider value={value}>
      {children}
    </CarPlayContext.Provider>
  );
};