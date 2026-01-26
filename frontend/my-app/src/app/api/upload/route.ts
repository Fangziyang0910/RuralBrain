import { NextRequest } from 'next/server';

export const runtime = 'nodejs'; // 上传文件需要 Node.js Runtime

export async function POST(request: NextRequest) {
  try {
    // 获取表单数据
    const formData = await request.formData();

    // 转发到后端
    const backendFormData = new FormData();
    const files = formData.getAll('files');

    for (const file of files) {
      if (file instanceof File) {
        // 将 File 对象转换为 Blob 并保留原始文件名
        const arrayBuffer = await file.arrayBuffer();
        const blob = new Blob([arrayBuffer], { type: file.type });
        backendFormData.append('files', blob, file.name);
      }
    }

    // 发送到后端
    const response = await fetch('http://localhost:8081/upload', {
      method: 'POST',
      body: backendFormData,
    });

    if (!response.ok) {
      throw new Error(`Upload failed: ${response.statusText}`);
    }

    // 返回后端响应
    const data = await response.json();
    return Response.json(data);
  } catch (error) {
    console.error('Upload proxy error:', error);
    return Response.json(
      { error: 'Upload failed' },
      { status: 500 }
    );
  }
}
