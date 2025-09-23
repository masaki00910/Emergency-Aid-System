/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  typescript: {
    ignoreBuildErrors: true,
  },
  eslint: {
    ignoreDuringBuilds: true,
  },
  output: 'standalone',
  // ビルド最適化
  experimental: {
    // メモリ使用量を削減
    webpackMemoryOptimizations: true,
  },
  // 画像最適化を無効化（ビルド時間短縮）
  images: {
    unoptimized: true
  },
  // SWCミニファイを使用（高速化）
  swcMinify: true,
  // 不要な機能を無効化
  poweredByHeader: false,
}

module.exports = nextConfig
