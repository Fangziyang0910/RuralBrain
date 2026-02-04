# RuralBrain 本地开发服务启动脚本 (Windows)
# 一键启动所有 4 个核心服务

param(
    [switch]$NoDetection = $false,    # 跳过检测服务
    [switch]$NoPlanning = $false,     # 跳过规划服务
    [switch]$NoFrontend = $false      # 跳过前端服务
)

# 颜色输出函数
function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

function Write-Success { Write-ColorOutput Green $args }
function Write-Info { Write-ColorOutput Cyan $args }
function Write-Warning { Write-ColorOutput Yellow $args }
function Write-Error { Write-ColorOutput Red $args }

# 显示标题
Write-Info "========================================"
Write-Info "  RuralBrain 服务启动脚本 (Windows)"
Write-Info "========================================"
Write-Output ""

# 获取项目根目录
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $ProjectRoot

Write-Info "项目目录: $ProjectRoot"
Write-Output ""

# 检查 uv
$uvCommand = Get-Command uv -ErrorAction SilentlyContinue
if (-not $uvCommand) {
    Write-Warning "未找到 uv，使用虚拟环境中的 Python"
    $pythonCommand = ".venv\Scripts\python.exe"
    if (-not (Test-Path $pythonCommand)) {
        Write-Error "虚拟环境不存在，请先运行: uv sync"
        exit 1
    }
} else {
    Write-Success "✓ uv 已安装"
    $pythonCommand = "uv"
    $runArgs = "run", "python"
}

Write-Output ""

# ========================================
# 启动检测服务网关 (端口 8001)
# ========================================
if (-not $NoDetection) {
    Write-Info "[1/4] 启动检测服务网关 (端口 8001)..."

    $detectionArgs = @()
    if ($pythonCommand -eq "uv") {
        $detectionArgs = $runArgs + "src/algorithms/api/main.py"
    } else {
        $detectionArgs = "src/algorithms/api/main.py"
    }

    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$ProjectRoot'; & '$pythonCommand' $detectionArgs"

    Write-Success "✓ 检测服务网关已启动"
    Write-Output "   服务地址: http://localhost:8001/docs"
    Write-Output ""

    Start-Sleep -Seconds 3
} else {
    Write-Warning "[1/4] 跳过检测服务网关"
    Write-Output ""
}

# ========================================
# 启动规划咨询服务 (端口 8003)
# ========================================
if (-not $NoPlanning) {
    Write-Info "[2/4] 启动规划咨询服务 (端口 8003)..."

    $planningArgs = @()
    if ($pythonCommand -eq "uv") {
        $planningArgs = $runArgs + "src/rag/service/main.py"
    } else {
        $planningArgs = "src/rag/service/main.py"
    }

    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$ProjectRoot'; & '$pythonCommand' $planningArgs"

    Write-Success "✓ 规划咨询服务已启动"
    Write-Output "   服务地址: http://localhost:8003/docs"
    Write-Output ""

    Start-Sleep -Seconds 3
} else {
    Write-Warning "[2/4] 跳过规划咨询服务"
    Write-Output ""
}

# ========================================
# 启动后端主服务 (端口 8081)
# ========================================
Write-Info "[3/4] 启动后端主服务 (端口 8081)..."

$backendArgs = @()
if ($pythonCommand -eq "uv") {
    $backendArgs = $runArgs + "run_server.py"
} else {
    $backendArgs = "run_server.py"
}

Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$ProjectRoot'; & '$pythonCommand' $backendArgs"

Write-Success "✓ 后端主服务已启动"
Write-Output "   服务地址: http://localhost:8081/docs"
Write-Output ""

Start-Sleep -Seconds 3

# ========================================
# 启动前端 (端口 3001)
# ========================================
if (-not $NoFrontend) {
    Write-Info "[4/4] 启动前端 (端口 3001)..."

    # 检查 node_modules
    if (-not (Test-Path "frontend/node_modules")) {
        Write-Warning "前端依赖未安装，正在安装..."
        Set-Location frontend
        npm install
        Set-Location $ProjectRoot
    }

    $frontendArgs = @()
    if ($pythonCommand -eq "uv") {
        $frontendArgs = $runArgs + "run_frontend.py"
    } else {
        $frontendArgs = "run_frontend.py"
    }

    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$ProjectRoot'; & '$pythonCommand' $frontendArgs"

    Write-Success "✓ 前端已启动"
    Write-Output "   服务地址: http://localhost:3001"
    Write-Output ""
} else {
    Write-Warning "[4/4] 跳过前端服务"
    Write-Output ""
}

# ========================================
# 启动完成
# ========================================
Write-Success "========================================"
Write-Success "  服务启动完成！"
Write-Success "========================================"
Write-Output ""
Write-Info "服务状态:"
if (-not $NoDetection) {
    Write-Output "  • 检测服务网关: http://localhost:8001/docs"
}
if (-not $NoPlanning) {
    Write-Output "  • 规划咨询服务: http://localhost:8003/docs"
}
Write-Output "  • 后端主服务:   http://localhost:8081/docs"
if (-not $NoFrontend) {
    Write-Output "  • 前端界面:     http://localhost:3001"
}
Write-Output ""
Write-Info "提示:"
Write-Output "  • 关闭服务: 直接关闭各个终端窗口"
Write-Output "  • 查看日志: 在对应服务的终端窗口查看"
Write-Output "  • 常见问题: 查看 LOCAL_DEV_GUIDE.md"
Write-Output ""

# 可选：等待用户按键后打开浏览器
$openBrowser = Read-Host "是否在浏览器中打开前端？(Y/N)"
if ($openBrowser -eq "Y" -or $openBrowser -eq "y") {
    Start-Process "http://localhost:3001"
}
