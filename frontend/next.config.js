/** @type {import('next').NextConfig} */
const nextConfig = {
  // --- THIS IS THE FIX ---
  // The 'rewrites' function must be a top-level key, parallel to 'images'.
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://backend:8000/api/:path*',
      },
    ]
  },

  images: {
    dangerouslyAllowSVG: true,
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'images.unsplash.com',
        port: '',
        pathname: '/**',
      },
      {
        protocol: 'https',
        hostname: 'placehold.co',
        port: '',
        pathname: '/**',
      },
      // Add common MLS image domains
      {
        protocol: 'https',
        hostname: '*.mlspin.com',
        port: '',
        pathname: '/**',
      },
      {
        protocol: 'https',
        hostname: '*.flexmls.com',
        port: '',
        pathname: '/**',
      },
      {
        protocol: 'https',
        hostname: '*.matrix.paragonrels.com',
        port: '',
        pathname: '/**',
      },
      // Allow any HTTPS image for flexibility
      {
        protocol: 'https',
        hostname: '**',
        port: '',
        pathname: '/**',
      },
    ],
  },
};

module.exports = nextConfig;