import { NextRequest } from 'next/server';

// 使用 Node.js Runtime 以支持环境变量和本地开发
export const runtime = 'nodejs';

export async function POST(request: NextRequest) {
  const abortController = new AbortController();

  try {
    // 优先使用环境变量，否则使用本地开发地址
    const backendBase = process.env.BACKEND_URL ?? 'http://localhost:8081';
    // 获取请求体
    const body = await request.json();

    // 创建到后端的流式请求
    const response = await fetch(`${backendBase}/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
      signal: abortController.signal,
    });

    // 创建可读流
    const reader = response.body?.getReader();
    if (!reader) {
      return new Response('No response body', { status: 500 });
    }

    // 创建 TransformStream 用于转发流式数据
    const stream = new ReadableStream({
      async start(controller) {
        let closed = false;
        const closeSafely = () => {
          if (closed) return;
          closed = true;
          try {
            controller.close();
          } catch {
            // ignore close errors when client already disconnected
          }
        };

        const cancelUpstream = () => {
          if (!abortController.signal.aborted) {
            abortController.abort();
          }
          void reader.cancel().catch(() => {
            // ignore reader cancel errors
          });
        };

        request.signal.addEventListener('abort', () => {
          cancelUpstream();
          closeSafely();
        }, { once: true });

        try {
          while (true) {
            if (request.signal.aborted) {
              cancelUpstream();
              break;
            }

            const { done, value } = await reader.read();
            if (done) break;
            if (!closed && value) {
              controller.enqueue(value);
            }
          }
        } catch (error) {
          if (!request.signal.aborted) {
            console.error('Stream error:', error);
          }
        } finally {
          cancelUpstream();
          closeSafely();
        }
      },
      cancel() {
        if (!abortController.signal.aborted) {
          abortController.abort();
        }
        return reader.cancel().catch(() => {
          // ignore reader cancel errors
        });
      },
    });

    return new Response(stream, {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'X-Accel-Buffering': 'no',
      },
    });
  } catch (error) {
    console.error('Proxy error:', error);
    return new Response(JSON.stringify({ error: 'Proxy error' }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' },
    });
  }
}
