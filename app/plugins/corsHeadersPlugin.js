// Plugin to add CORS headers for cross-origin isolation
// This is required for the stream buffer to work.

const corsHeadersPlugin = {
  name: 'configure-response-headers',
  configureServer(server) {
    server.middlewares.use((req, res, next) => {
      res.setHeader('Cross-Origin-Opener-Policy', 'same-origin');
      res.setHeader('Cross-Origin-Embedder-Policy', 'require-corp');
      next();
    });
  },
};

module.exports = corsHeadersPlugin;