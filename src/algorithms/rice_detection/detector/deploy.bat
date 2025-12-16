@echo off
echo ========================================
echo 🚀 构建并启动大米检测服务 (Docker)
echo ========================================

REM 停止并删除现有容器
echo 🛑 停止现有容器...
docker-compose down

REM 构建镜像
echo 📦 构建Docker镜像...
docker-compose build --no-cache

REM 启动服务
echo 🚀 启动服务...
docker-compose up -d

REM 等待服务启动
echo ⏳ 等待服务启动...
timeout /t 10 /nobreak > nul

REM 检查服务状态
echo 🔍 检查服务状态...
docker-compose ps

echo ========================================
echo ✅ 部署完成！
echo 📍 服务地址: http://localhost:8081
echo 📖 API文档: http://localhost:8081/docs
echo ========================================
echo.
echo 📝 查看日志: docker-compose logs -f
echo 🛑 停止服务: docker-compose down
echo 🔄 重启服务: docker-compose restart
echo.
pause