/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    // --- MODIFIED: Add dangerouslyAllowSVG property ---
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