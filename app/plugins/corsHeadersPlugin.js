// Plugin to add CORS headers for cross-origin isolation
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