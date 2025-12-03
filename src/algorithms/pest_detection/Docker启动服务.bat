@echo off
chcp 65001 >nul
echo.
echo ============================================
echo      害虫检测API - Docker快速启动
echo ============================================
echo.

cd /d "%~dp0detector"

echo 检查Docker服务状态...
docker-compose ps | findstr "insect-detector-api" | findstr "Up" >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ 服务已运行中
    echo.
    echo 🌐 访问地址:
    echo    - API文档: http://localhost:8001/docs
    echo    - 健康检查: http://localhost:8001/health
    echo.
    set /p restart=服务已启动，是否重启? (y/n): 
    if /i "%restart%"=="y" (
        echo 正在重启服务...
        docker-compose restart
        echo ✅ 服务重启完成！
    )
) else (
    echo 🚀 正在启动Docker服务...
    echo 执行命令: docker-compose up -d --build
    docker-compose up -d --build
    if %errorlevel% equ 0 (
        echo.
        echo ✅ 服务启动成功！
        echo.
        echo 🌐 访问地址:
        echo    - API文档: http://localhost:8001/docs
        echo    - 健康检查: http://localhost:8001/health
        echo    - 主页: http://localhost:8001
    ) else (
        echo ❌ 服务启动失败
        echo.
        echo 请检查:
        echo 1. Docker Desktop 是否已安装并启动
        echo 2. 模型文件是否存在 (detector/models/best.pt)
        echo 3. 端口8001是否被占用
    )
)

echo.
echo 💡 管理命令:
echo    - 查看状态: docker-compose ps
echo    - 查看日志: docker-compose logs -f
echo    - 停止服务: docker-compose stop
echo    - 删除容器: docker-compose down
echo.
pause