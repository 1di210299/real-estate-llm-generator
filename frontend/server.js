import express from 'express';
import path from 'path';
import { fileURLToPath } from 'url';
import { createProxyMiddleware } from 'http-proxy-middleware';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = process.env.PORT || 3000;

// Backend URL - use internal routing in App Platform
const BACKEND_URL = process.env.BACKEND_URL || 'http://web:8080';

console.log('🔧 Frontend Server Config:');
console.log('  - Port:', PORT);
console.log('  - Backend URL:', BACKEND_URL);

// Proxy API routes to backend
const apiPaths = ['/chat', '/properties', '/conversations', '/documents', '/ingest', '/admin', '/auth', '/tenants'];

apiPaths.forEach(apiPath => {
  app.use(apiPath, createProxyMiddleware({
    target: BACKEND_URL,
    changeOrigin: true,
    logLevel: 'debug',
    onProxyReq: (proxyReq, req, res) => {
      console.log(`🔀 Proxying ${req.method} ${req.url} -> ${BACKEND_URL}${req.url}`);
    },
    onError: (err, req, res) => {
      console.error('❌ Proxy error:', err.message);
      res.status(502).json({ error: 'Bad Gateway', message: err.message });
    }
  }));
});

// Serve static files from dist directory
app.use(express.static(path.join(__dirname, 'dist')));

// Health check endpoint
app.get('/health', (req, res) => {
  res.status(200).json({ status: 'healthy' });
});

// SPA fallback - all routes serve index.html
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'dist', 'index.html'));
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`✅ Frontend server running on port ${PORT}`);
  console.log(`✅ Proxying API routes to ${BACKEND_URL}`);
});

