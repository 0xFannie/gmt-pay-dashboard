@echo off
REM GMT Pay Dashboard 启动脚本（Windows版，带自动刷新）

echo 🚀 启动 GMT Pay Dashboard...

REM 检查Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ 未找到Python，请先安装Python
    pause
    exit /b 1
)

REM 检查依赖
python -c "import streamlit" >nul 2>nul
if %errorlevel% neq 0 (
    echo 📦 安装依赖...
    pip install -r requirements.txt
)

REM 检查.env文件
if not exist ".env" (
    echo ⚠️  警告: 未找到.env文件，请配置API Keys
)

REM 启动自动刷新服务（后台运行）
echo 🔄 启动数据自动刷新服务...
start /B python auto_refresh_data.py > data_refresh.log 2>&1

REM 等待1秒
timeout /t 1 /nobreak >nul

REM 启动Dashboard
echo 📊 启动Dashboard...
python -m streamlit run dashboard_v3_dynamic.py --server.port=8501 --server.address=0.0.0.0

pause

