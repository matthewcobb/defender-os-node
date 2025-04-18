import React from 'react';
import './App.css';
import { CarPlayProvider } from './features/carplay/context/CarPlayContext';
import { CarPlayDisplay } from './features/carplay/components/CarPlayDisplay';

function App() {
  const width = window.innerWidth;
  const height = window.innerHeight;

  return (
    <CarPlayProvider width={width} height={height}>
      <div className="App">
        <CarPlayDisplay />
      </div>
    </CarPlayProvider>
  );
}

export default App;