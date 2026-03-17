import { NextResponse } from 'next/server';

// 使用 Node.js Runtime 以支持环境变量
export const runtime = 'nodejs';

export async function GET() {
  try {
    // 优先使用环境变量，否则使用本地开发地址
    const backendBase = process.env.BACKEND_URL ?? 'http://localhost:8081';

    const response = await fetch(`${backendBase}/models`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Backend error: ${response.status}`);
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Models API proxy error:', error);
    return NextResponse.json(
      { error: 'Failed to fetch models' },
      { status: 500 }
    );
  }
}