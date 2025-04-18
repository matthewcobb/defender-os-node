const path = require('path');
const fs = require('fs');

// Plugin to serve worklet files directly
const serveWorkletPlugin = {
  name: 'serve-worklet-files',
  configureServer(server) {
    server.middlewares.use((req, res, next) => {
      // Explicitly handle requests for the recorder worklet
      if (req.url === '/node_modules/.vite/deps/recorder.worklet.js') {
        const recorderPath = path.resolve(__dirname, '../public/recorder.worklet.js');
        if (fs.existsSync(recorderPath)) {
          res.setHeader('Content-Type', 'application/javascript');
          res.end(fs.readFileSync(recorderPath, 'utf8'));
          return;
        }
      }

      // Explicitly handle requests for the audio worklet
      if (req.url === '/node_modules/.vite/deps/audio.worklet.js') {
        const audioPath = path.resolve(__dirname, '../public/audio.worklet.js');
        if (fs.existsSync(audioPath)) {
          res.setHeader('Content-Type', 'application/javascript');
          res.end(fs.readFileSync(audioPath, 'utf8'));
          return;
        }
      }

      next();
    });
  },
};

module.exports = serveWorkletPlugin;