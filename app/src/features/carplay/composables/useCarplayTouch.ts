import { ref } from 'vue';
import { TouchAction } from 'node-carplay/web';
import { CarPlayWorker } from '../../../workers/types';

export function useCarplayTouch(worker: CarPlayWorker, width: number, height: number) {
  const pointerdown = ref(false);

  const sendTouchEvent = (e: PointerEvent) => {
    let action = TouchAction.Up;
    if (e.type === 'pointerdown') {
      action = TouchAction.Down;
      pointerdown.value = true;
    } else if (pointerdown.value) {
      switch (e.type) {
        case 'pointermove':
          action = TouchAction.Move;
          break;
        case 'pointerup':
        case 'pointercancel':
        case 'pointerout':
          pointerdown.value = false;
          action = TouchAction.Up;
          break;
      }
    } else {
      return;
    }

    const { offsetX: x, offsetY: y } = e;
    worker.postMessage({
      type: 'touch',
      payload: { x: x / width, y: y / height, action },
    });
  };

  return sendTouchEvent;
}