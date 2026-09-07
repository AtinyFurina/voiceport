# 一键启动服务端（先设环境变量再运行）
# 用法: 在 PowerShell 里 .\run_server.ps1

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

# 首次运行自动创建 venv + 装依赖
if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "创建虚拟环境..."
    python -m venv .venv
    .\.venv\Scripts\python.exe -m pip install --quiet --disable-pip-version-check -e ".[dev]"
}

# 密钥从环境变量读取（见 config.py）；未设置则提示
if (-not $env:IFLYTEK_APPID -and -not $env:SILICONFLOW_API_KEY) {
    Write-Warning "未检测到 STT 密钥（IFLYTEK_APPID / SILICONFLOW_API_KEY），STT 调用将失败"
}
if (-not $env:DEEPSEEK_API_KEY) {
    Write-Warning "未检测到 DEEPSEEK_API_KEY，修改/偏好总结将失败"
}

Write-Host "启动服务端 (端口 $($env:PASSPORT_PORT ?? 8765))..."
.\.venv\Scripts\python.exe ws_server.py
