@echo off
echo ============================================================
echo RuralBrain 前端服务启动中...
echo ============================================================
echo.

REM 切换到项目根目录
cd /d "%~dp0..\..\"
cd frontend\my-app

REM 检查是否已安装依赖
if not exist "node_modules" (
    echo 首次运行，正在安装依赖...
    call npm install
)

echo.
echo 启动前端开发服务器...
echo 访问地址: http://localhost:3000
echo.

call npm run dev
