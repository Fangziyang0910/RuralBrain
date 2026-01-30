/** @type {import('next').NextConfig} */
const backendBase = process.env.BACKEND_URL ?? 'http://backend:8080';

const nextConfig = {
  // 开启 React 严格模式
  reactStrictMode: true,
  output: 'standalone',
  async rewrites() {
    return [
      // /api 路由现在由 Route Handler 处理（支持流式响应）
      // 保留静态资源的代理规则
      {
        source: '/pest_results/:path*',
        destination: `${backendBase}/pest_results/:path*`,
      },
      {
        source: '/cow_results/:path*',
        destination: `${backendBase}/cow_results/:path*`,
      },
      {
        source: '/rice_results/:path*',
        destination: `${backendBase}/rice_results/:path*`,
      },
    ];
  },
};

export default nextConfig;
