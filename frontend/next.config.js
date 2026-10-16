/** @type {import('next').NextConfig} */
const backendApiUrl = (process.env.BACKEND_API_URL || 'http://localhost:8000').replace(/\/$/, '');

const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      // The current FastAPI app exposes health routes at the root, not under /api.
      {
        source: '/backend-api/health',
        destination: `${backendApiUrl}/health`,
      },
      {
        source: '/backend-api/health/:path*',
        destination: `${backendApiUrl}/health/:path*`,
      },
      // Business API routes currently live under /api (for example /api/leads).
      {
        source: '/backend-api/:path*',
        destination: `${backendApiUrl}/api/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
