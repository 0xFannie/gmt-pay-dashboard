# GMT Pay Dashboard Docker 镜像

FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . .

# 暴露端口
EXPOSE 8501

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# 启动命令（同时启动Dashboard和自动刷新）
CMD python auto_refresh_data.py & \
    streamlit run dashboard_v3_dynamic.py \
    --server.port=8501 \
    --server.address=0.0.0.0 \
    --server.headless=true

