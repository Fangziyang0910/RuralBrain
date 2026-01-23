@echo off
chcp 65001 >nul 2>&1
echo.
echo ============================================
echo 🚀 农村智能检测系统 - 统一部署脚本
echo ============================================
echo.

REM 检查Docker是否安装
where docker >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 错误: Docker未安装或未添加到PATH环境变量
    echo 请先安装Docker并确保其可用
    pause
    exit /b 1
)

REM 检查Docker Compose是否可用
docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 错误: Docker Compose未安装
    echo 请先安装Docker Compose
    pause
    exit /b 1
)

REM 检查项目结构
echo 📁 检查项目结构...
if not exist "src\algorithms\pest_detection" (
    echo ❌ 错误: 病虫害检测服务目录不存在
    pause
    exit /b 1
)

if not exist "src\algorithms\rice_detection" (
    echo ❌ 错误: 大米识别服务目录不存在
    pause
    exit /b 1
)

if not exist "src\algorithms\cow_detection" (
    echo ❌ 错误: 奶牛检测服务目录不存在
    pause
    exit /b 1
)

echo ✅ 项目结构检查通过

REM 检查是否已存在镜像
echo.
echo 🔍 检查现有镜像...
docker images | findstr "ruralbrain-pest-detector"
if %errorlevel% equ 0 (
    echo ✅ 病虫害检测服务镜像已存在
    set PEST_IMAGE_EXISTS=true
) else (
    echo 📝 病虫害检测服务镜像不存在，需要构建
    set PEST_IMAGE_EXISTS=false
)

docker images | findstr "ruralbrain-rice-detector"
if %errorlevel% equ 0 (
    echo ✅ 大米识别服务镜像已存在
    set RICE_IMAGE_EXISTS=true
) else (
    echo 📝 大米识别服务镜像不存在，需要构建
    set RICE_IMAGE_EXISTS=false
)

docker images | findstr "ruralbrain-cow-detector"
if %errorlevel% equ 0 (
    echo ✅ 奶牛检测服务镜像已存在
    set COW_IMAGE_EXISTS=true
) else (
    echo 📝 奶牛检测服务镜像不存在，需要构建
    set COW_IMAGE_EXISTS=false
)

REM 统计需要构建的服务数量
set SERVICES_TO_BUILD=0
if "%PEST_IMAGE_EXISTS%"=="false" set /a SERVICES_TO_BUILD+=1
if "%RICE_IMAGE_EXISTS%"=="false" set /a SERVICES_TO_BUILD+=1
if "%COW_IMAGE_EXISTS%"=="false" set /a SERVICES_TO_BUILD+=1

REM 询问是否重新构建已存在的镜像
echo.
if %SERVICES_TO_BUILD% equ 0 (
    echo ✅ 检测到所有服务镜像已存在
    echo 是否重新构建所有镜像？(Y/N，默认:N)
    echo 注意：选择N将直接使用现有镜像启动服务
) else (
    echo 📝 检测到 %SERVICES_TO_BUILD% 个服务需要构建
    echo 是否重新构建已存在的镜像？(Y/N，默认:N)
    echo 注意：选择N将只构建不存在的镜像，保留已有的部署
)
set /p rebuild_images=
if "%rebuild_images%"=="" set rebuild_images=N

REM 停止并移除现有容器（仅在需要构建或用户选择重新构建时）
if %SERVICES_TO_BUILD% gtr 0 (
    echo.
    echo 🛑 停止现有服务...
    docker-compose -f docker-compose.all.yml down
) else (
    if /i "%rebuild_images%"=="Y" (
        echo.
        echo 🛑 停止现有服务...
        docker-compose -f docker-compose.all.yml down
    ) else (
        echo.
        echo ⏭️ 检测到镜像已存在且无需重新构建
        echo 🔄 准备重启现有服务...
    )
)

REM 清理旧镜像（可选）- 只清理未被使用的镜像
if /i "%rebuild_images%"=="Y" (
    echo.
    echo 🧹 清理未被使用的旧镜像...
    echo 是否要清理未被容器使用的旧镜像？(Y/N)
    set /p clean_images=
    if /i "%clean_images%"=="Y" (
        echo 正在清理未被使用的旧镜像...
        docker image prune -f
        echo ✅ 清理完成（注意：这不会删除正在运行的容器）
    )
)

REM 根据镜像存在情况决定构建策略
echo.
echo 🔨 开始处理服务...
echo.

if /i "%rebuild_images%"=="Y" (
    echo 🔄 强制重新构建所有服务
    set SERVICES_TO_BUILD=3
) else (
    if %SERVICES_TO_BUILD% equ 0 (
        echo ✅ 所有服务镜像已存在，跳过构建阶段
        echo 🚀 准备直接启动服务...
    ) else (
        echo 📝 有 %SERVICES_TO_BUILD% 个服务需要构建
    )
)

REM 构建病虫害检测服务
if "%PEST_IMAGE_EXISTS%"=="false" (
    echo 🐛 构建病虫害检测服务...
    docker-compose -f docker-compose.all.yml build pest-detector
    if !errorlevel! neq 0 (
        echo ❌ 病虫害检测服务构建失败，请检查错误信息
        pause
        exit /b 1
    )
    echo ✅ 病虫害检测服务构建成功
) else (
    if /i "%rebuild_images%"=="Y" (
        echo 🐛 重新构建病虫害检测服务...
        docker-compose -f docker-compose.all.yml build pest-detector
        if !errorlevel! neq 0 (
            echo ❌ 病虫害检测服务构建失败，请检查错误信息
            pause
            exit /b 1
        )
        echo ✅ 病虫害检测服务构建成功
    ) else (
        echo ⏭️ 跳过病虫害检测服务构建（镜像已存在）
    )
)

REM 构建大米识别服务
if "%RICE_IMAGE_EXISTS%"=="false" (
    echo 🌾 构建大米识别服务...
    docker-compose -f docker-compose.all.yml build rice-detector
    if %errorlevel% neq 0 (
        echo ❌ 大米识别服务构建失败，请检查错误信息
        pause
        exit /b 1
    )
    echo ✅ 大米识别服务构建成功
) else (
    if /i "%rebuild_images%"=="Y" (
        echo 🌾 重新构建大米识别服务...
        docker-compose -f docker-compose.all.yml build rice-detector
        if %errorlevel% neq 0 (
            echo ❌ 大米识别服务构建失败，请检查错误信息
            pause
            exit /b 1
        )
        echo ✅ 大米识别服务构建成功
    ) else (
        echo ⏭️ 跳过大米识别服务构建（镜像已存在）
    )
)

REM 构建奶牛检测服务
if "%COW_IMAGE_EXISTS%"=="false" (
    echo 🐄 构建奶牛检测服务...
    docker-compose -f docker-compose.all.yml build cow-detector
    if %errorlevel% neq 0 (
        echo ❌ 奶牛检测服务构建失败，请检查错误信息
        pause
        exit /b 1
    )
    echo ✅ 奶牛检测服务构建成功
) else (
    if /i "%rebuild_images%"=="Y" (
        echo 🐄 重新构建奶牛检测服务...
        docker-compose -f docker-compose.all.yml build cow-detector
        if %errorlevel% neq 0 (
            echo ❌ 奶牛检测服务构建失败，请检查错误信息
            pause
            exit /b 1
        )
        echo ✅ 奶牛检测服务构建成功
    ) else (
        echo ⏭️ 跳过奶牛检测服务构建（镜像已存在）
    )
)
    echo 🐄 构建奶牛检测服务...
    docker-compose -f docker-compose.all.yml build cow-detector
    if %errorlevel% neq 0 (
        echo ❌ 奶牛检测服务构建失败，请检查错误信息
        pause
        exit /b 1
    )
    echo ✅ 奶牛检测服务构建成功
) else (
    echo ⏭️ 跳过奶牛检测服务构建（镜像已存在）
)

if %SERVICES_TO_BUILD% gtr 0 (
    echo ✅ 服务构建完成
) else (
    if /i "%rebuild_images%"=="Y" (
        echo ✅ 服务重新构建完成
    ) else (
        echo ✅ 使用现有镜像，无需构建
    )
)

REM 启动所有服务
echo.
echo 🚀 启动所有服务...
docker-compose -f docker-compose.all.yml up -d

if %errorlevel% neq 0 (
    echo ❌ 启动失败，请检查错误信息
    pause
    exit /b 1
)

echo ✅ 服务启动成功

REM 等待服务启动
echo.
echo ⏳ 等待服务启动...
timeout /t 10 /nobreak >nul

REM 检查服务状态
echo.
echo 🔍 检查服务状态...
echo.

REM 检查病虫害检测服务
echo 🐛 病虫害检测服务 (端口: 8001):
curl -s -o nul -w "状态: %{http_code}, 响应时间: %{time_total}s\n" http://localhost:8001/health || echo ❌ 服务未响应

REM 检查大米识别服务
echo 🌾 大米识别服务 (端口: 8081):
curl -s -o nul -w "状态: %{http_code}, 响应时间: %{time_total}s\n" http://localhost:8081/health || echo ❌ 服务未响应

REM 检查奶牛检测服务
echo 🐄 奶牛检测服务 (端口: 8002):
curl -s -o nul -w "状态: %{http_code}, 响应时间: %{time_total}s\n" http://localhost:8002/health || echo ❌ 服务未响应

echo.
echo ============================================
echo ✅ 部署完成！
echo ============================================
echo.
echo 📋 服务信息:
echo   🐛 病虫害检测服务: http://localhost:8001/docs
echo   🌾 大米识别服务:   http://localhost:8081/docs
echo   🐄 奶牛检测服务:   http://localhost:8002/docs
echo.
echo 📁 查看日志命令:
echo   docker-compose -f docker-compose.all.yml logs -f
echo.
echo 🛑 停止服务命令:
echo   docker-compose -f docker-compose.all.yml down
echo.
echo 🔄 重启服务命令:
echo   docker-compose -f docker-compose.all.yml restart
echo.
pause