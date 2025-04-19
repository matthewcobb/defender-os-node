const express = require('express');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;

// Set security headers for all responses
app.use((req, res, next) => {
  res.set('Cross-Origin-Opener-Policy', 'same-origin');
  res.set('Cross-Origin-Embedder-Policy', 'require-corp');
  next();
});

// Serve static files
app.use(express.static(path.join(__dirname, 'build')));

// Handle routes based on file extension
app.use((req, res) => {
  // If the path has a file extension, it should have been caught by the static middleware
  // Otherwise serve the index.html file for SPA routing
  res.sendFile(path.join(__dirname, 'build', 'index.html'));
});

app.listen(PORT, () => {
  console.log(`Server is running on http://localhost:${PORT}`);
});
