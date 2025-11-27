@echo off
REM FastAPI测试启动脚本 (Windows)
REM 用于快速启动FastAPI服务器和运行测试

setlocal enabledelayedexpansion

echo ========================================
echo FastAPI测试启动脚本
echo ========================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python 3.8或更高版本
    pause
    exit /b 1
)

REM 显示菜单
:menu
echo 请选择操作:
echo 1. 启动FastAPI服务器 (开发模式)
echo 2. 启动FastAPI服务器 (生产模式)
echo 3. 运行API测试
echo 4. 安装依赖
echo 5. 查看API文档
echo 6. 退出
echo.
set /p choice=请输入选项 (1-6): 

if "%choice%"=="1" goto start_dev
if "%choice%"=="2" goto start_prod
if "%choice%"=="3" goto run_tests
if "%choice%"=="4" goto install_deps
if "%choice%"=="5" goto view_docs
if "%choice%"=="6" goto end
echo 无效选项，请重新选择
goto menu

:start_dev
echo.
echo 启动FastAPI服务器 (开发模式)...
echo 服务器地址: http://127.0.0.1:8000
echo API文档: http://127.0.0.1:8000/docs
echo 按 Ctrl+C 停止服务器
echo.
python tests/run_fastapi_server.py --reload
goto menu

:start_prod
echo.
echo 启动FastAPI服务器 (生产模式)...
echo 服务器地址: http://127.0.0.1:8000
echo API文档: http://127.0.0.1:8000/docs
echo 按 Ctrl+C 停止服务器
echo.
python tests/run_fastapi_server.py --workers 4
goto menu

:run_tests
echo.
echo 运行API测试...
echo 请确保FastAPI服务器正在运行 (http://127.0.0.1:8000)
echo.
python tests/test_fastapi_client.py
echo.
pause
goto menu

:install_deps
echo.
echo 安装FastAPI测试依赖...
echo.
pip install -r tests/requirements.txt
echo.
echo 依赖安装完成!
echo.
pause
goto menu

:view_docs
echo.
echo 打开API文档...
echo.
start http://127.0.0.1:8000/docs
goto menu

:end
echo.
echo 再见!
echo.
pause