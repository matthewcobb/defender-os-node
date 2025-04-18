const path = require('path');
const fs = require('fs');

// Copy worklet files to public directory
const copyWorkletPlugin = {
  name: 'copy-worklet-plugin',
  buildStart() {
    // Ensure public directory exists
    if (!fs.existsSync(path.resolve(__dirname, '../public'))) {
      fs.mkdirSync(path.resolve(__dirname, '../public'));
    }

    // Copy audio worklet file
    const audioWorkletPath = path.resolve(__dirname, '../node_modules/pcm-ringbuf-player/dist/audio.worklet.js');
    const audioDestPath = path.resolve(__dirname, '../public/audio.worklet.js');
    fs.copyFileSync(audioWorkletPath, audioDestPath);
    console.log('Copied audio worklet file to public directory');

    // Copy recorder worklet file
    const recorderWorkletPath = path.resolve(__dirname, '../node_modules/node-carplay/dist/web/recorder.worklet.js');
    const recorderDestPath = path.resolve(__dirname, '../public/recorder.worklet.js');
    fs.copyFileSync(recorderWorkletPath, recorderDestPath);
    console.log('Copied recorder worklet file to public directory');
  }
};

module.exports = copyWorkletPlugin;