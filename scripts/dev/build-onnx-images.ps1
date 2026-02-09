# RuralBrain 轻量级镜像快速构建脚本 (Windows PowerShell)
# 使用 ONNX Runtime，减少依赖和镜像体积

$ErrorActionPreference = "Stop"

Write-Host "==================================" -ForegroundColor Cyan
Write-Host "RuralBrain ONNX Image Builder" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is running
try {
    docker info > $null 2>&1
} catch {
    Write-Host "Error: Docker is not running. Please start Docker first." -ForegroundColor Red
    exit 1
}

# Change to project root directory
$projectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $projectRoot

Write-Host "Project Directory: $projectRoot" -ForegroundColor Yellow
Write-Host ""

# Define images and build order
$buildOrder = @(
    @{ Name = "detection-service"; Dockerfile = "docker/Dockerfile.detection.onnx" },
    @{ Name = "planning-service"; Dockerfile = "docker/Dockerfile.planning.onnx" },
    @{ Name = "backend"; Dockerfile = "docker/Dockerfile.backend.onnx" },
    @{ Name = "frontend"; Dockerfile = "docker/Dockerfile.frontend.onnx" }
)

Write-Host "Build Order: $($buildOrder.Name -join ', ')" -ForegroundColor Yellow
Write-Host ""

# Build each image
foreach ($service in $buildOrder) {
    Write-Host "----------------------------------------" -ForegroundColor Cyan
    Write-Host "Building: $($service.Name)" -ForegroundColor Cyan
    Write-Host "Dockerfile: $($service.Dockerfile)" -ForegroundColor Gray
    Write-Host "----------------------------------------" -ForegroundColor Cyan

    $dockerfile = $service.Dockerfile
    $imageName = "ruralbrain-$($service.Name):onnx"

    $buildArgs = @("build", "-f", $dockerfile, "-t", $imageName)

    if ($service.Name -eq "frontend") {
        $buildArgs += @("--build-arg", "NEXT_PUBLIC_API_URL=http://localhost:8081", "./frontend")
    } else {
        $buildArgs += @(".")
    }

    # Run docker build and display output in real-time
    & docker @buildArgs

    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ $($service.Name) built successfully" -ForegroundColor Green
        Write-Host ""
    } else {
        Write-Host "✗ $($service.Name) build failed" -ForegroundColor Red
        exit 1
    }
}

Write-Host "==================================" -ForegroundColor Cyan
Write-Host "All images built successfully!" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Built Images:" -ForegroundColor Yellow
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}" | grep "ruralbrain.*onnx"

Write-Host ""
Write-Host "Image Sizes:" -ForegroundColor Yellow
foreach ($service in $buildOrder) {
    $imageName = "ruralbrain-$($service.Name):onnx"
    $size = docker images $imageName --format "{{.Size}}"
    Write-Host "  - $($service.Name): $size" -ForegroundColor White
}

Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Start services: docker-compose -f docker-compose.onnx.yml up -d" -ForegroundColor White
Write-Host "  2. View logs: docker-compose -f docker-compose.onnx.yml logs -f" -ForegroundColor White
Write-Host "  3. Open frontend: http://localhost:3001" -ForegroundColor White
