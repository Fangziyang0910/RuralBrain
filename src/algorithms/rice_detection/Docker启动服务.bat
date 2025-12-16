@echo off
echo ========================================
echo 🚀 启动大米检测服务 (Docker)
echo ========================================

REM 检查Docker是否运行
docker version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker未运行，请先启动Docker Desktop
    pause
    exit /b 1
)

REM 启动服务
echo 🚀 启动服务...
docker-compose up -d

REM 等待服务启动
echo ⏳ 等待服务启动...
timeout /t 15 /nobreak > nul

REM 检查服务状态
echo 🔍 检查服务状态...
docker-compose ps

REM 测试健康检查
echo 🔍 测试健康检查...
curl -f http://localhost:8081/health >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ 服务运行正常！
) else (
    echo ⚠️ 服务可能还在启动中，请稍后再试
)

echo ========================================
echo ✅ 服务启动完成！
echo 📍 服务地址: http://localhost:8081
echo 📖 API文档: http://localhost:8081/docs
echo ========================================
echo.
echo 📝 查看日志: docker-compose logs -f
echo 🛑 停止服务: docker-compose down
echo 🔄 重启服务: docker-compose restart
echo.
pause