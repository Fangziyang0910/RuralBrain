/** @type {import('next').NextConfig} */
const nextConfig = {
  // 开启 React 严格模式
  reactStrictMode: true,
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8080/:path*',
      },
      {
        source: '/pest_results/:path*',
        destination: 'http://localhost:8080/pest_results/:path*',
      },
      {
        source: '/cow_results/:path*',
        destination: 'http://localhost:8080/cow_results/:path*',
      },
      {
        source: '/rice_results/:path*',
        destination: 'http://localhost:8080/rice_results/:path*',
      },
    ];
  },
};

export default nextConfig;
