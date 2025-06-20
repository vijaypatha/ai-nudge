/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Allows external image domains if needed, though <img> is used for placeholders
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'via.placeholder.com', // Example placeholder domain
      },
    ],
  },
};

module.exports = nextConfig;