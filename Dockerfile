# Nebula AI Core - 生产部署镜像
# 作者: 晨星
# 用法: docker build -t nebula-ai-core . && docker run -p 8000:8000 nebula-ai-core
FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=utf-8 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# 先装依赖层（利用缓存）
COPY requirements.txt requirements-prod.txt ./
RUN pip install -r requirements.txt -r requirements-prod.txt

# 再拷贝源码
COPY src ./src
COPY samples ./samples

ENV PYTHONPATH=/app/src
EXPOSE 8000

CMD ["python", "-m", "uvicorn", "nebula.api.server:app", "--host", "0.0.0.0", "--port", "8000"]
