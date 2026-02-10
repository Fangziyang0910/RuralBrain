/** @type {import('next').NextConfig} */
const backendBase = process.env.BACKEND_URL ?? 'http://backend:8081';

const nextConfig = {
  // 开启 React 严格模式
  reactStrictMode: true,
  // standalone 模式用于生产环境 Docker 部署
  // 开发环境 (npm run dev) 不受此配置影响
  output: 'standalone',
  // 配置 webpack 忽略路径大小写警告
  webpack: (config, { isServer }) => {
    config.infrastructureLogging = {
      ...config.infrastructureLogging,
      level: 'error',
    };
    return config;
  },
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
