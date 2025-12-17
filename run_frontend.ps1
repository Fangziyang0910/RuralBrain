# RuralBrain 前端启动脚本

Write-Host "=" -NoNewline
Write-Host ("=" * 60)
Write-Host "RuralBrain 前端服务启动中..."
Write-Host "=" -NoNewline
Write-Host ("=" * 60)
Write-Host ""

Set-Location frontend/my-app

# 检查是否已安装依赖
if (-not (Test-Path "node_modules")) {
    Write-Host "首次运行，正在安装依赖..."
    npm install
}

Write-Host ""
Write-Host "启动前端开发服务器..."
Write-Host "访问地址: http://localhost:3000"
Write-Host ""

npm run dev
