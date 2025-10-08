#!/bin/bash
# GMT Pay Dashboard 启动脚本（带自动刷新）

echo "🚀 启动 GMT Pay Dashboard..."

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到Python3，请先安装Python"
    exit 1
fi

# 检查依赖
if ! python3 -c "import streamlit" &> /dev/null; then
    echo "📦 安装依赖..."
    pip3 install -r requirements.txt
fi

# 检查.env文件
if [ ! -f ".env" ]; then
    echo "⚠️  警告: 未找到.env文件，请配置API Keys"
fi

# 启动自动刷新服务（后台运行）
echo "🔄 启动数据自动刷新服务..."
nohup python3 auto_refresh_data.py > data_refresh.log 2>&1 &
REFRESH_PID=$!
echo "   数据刷新服务 PID: $REFRESH_PID"

# 等待1秒
sleep 1

# 启动Dashboard
echo "📊 启动Dashboard..."
python3 -m streamlit run dashboard_v3_dynamic.py --server.port=8501 --server.address=0.0.0.0

# 清理：当Dashboard停止时，也停止自动刷新
echo "🛑 停止自动刷新服务..."
kill $REFRESH_PID 2>/dev/null

