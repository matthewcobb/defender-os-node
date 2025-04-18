import React from 'react';
import { RotatingLines } from 'react-loader-spinner';
import { useCarPlay } from '../context/CarPlayContext';

export const CarPlayDisplay: React.FC = () => {
  const { isPlugged, deviceFound, isLoading, checkDevice, sendTouchEvent, canvasRef } = useCarPlay();

  return (
    <div style={{ height: '100%', touchAction: 'none' }} className="carplay-display">
      {isLoading && (
        <div
          style={{
            position: 'absolute',
            width: '100%',
            height: '100%',
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
          }}
        >
          {deviceFound === false && (
            <button onClick={() => checkDevice(true)} rel="noopener noreferrer">
              Plug-In Carplay Dongle and Press
            </button>
          )}
          {deviceFound === true && (
            <RotatingLines
              strokeColor="grey"
              strokeWidth="5"
              animationDuration="0.75"
              width="96"
              visible={true}
            />
          )}
        </div>
      )}
      <div
        id="videoContainer"
        onPointerDown={sendTouchEvent}
        onPointerMove={sendTouchEvent}
        onPointerUp={sendTouchEvent}
        onPointerCancel={sendTouchEvent}
        onPointerOut={sendTouchEvent}
        style={{
          height: '100%',
          width: '100%',
          padding: 0,
          margin: 0,
          display: 'flex',
        }}
      >
        <canvas
          ref={canvasRef}
          id="video"
          style={isPlugged ? { height: '100%' } : { display: 'none' }}
        />
      </div>
    </div>
  );
};