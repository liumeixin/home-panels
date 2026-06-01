from python:3.11-slim

WORKDIR /app

# 安装依赖
RUN pip install --no-cache-dir flask flask-cors

# 复制代码
COPY backend/app.py /app/
COPY backend/templates /app/templates

# 创建非 root 用户
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app

USER 1000

EXPOSE 8080

CMD ["python", "app.py"]