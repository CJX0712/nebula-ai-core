# Nebula AI Core - 生产部署镜像
# 作者: 晨星
# 用法: docker build -t nebula-ai-core . && docker run -p 8000:8000 nebula-ai-core
#
# requirements-prod.txt (faiss / fastembed / llama-cpp-python 等重后端) 默认不安装 ——
# 镜像默认使用 requirements.txt 的最小闭包离线栈, 开箱即用。需要生产后端时:
#   docker build --build-arg WITH_PROD=1 -t nebula-ai-core .
FROM python:3.14-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=utf-8 \
    PIP_NO_CACHE_DIR=1

ARG WITH_PROD=0

WORKDIR /app

# 先装依赖层（利用缓存）
COPY requirements.txt requirements-prod.txt ./
RUN set -eux; \
    if [ "$WITH_PROD" = "1" ]; then \
        apt-get update; \
        apt-get install -y --no-install-recommends build-essential cmake; \
        rm -rf /var/lib/apt/lists/*; \
        pip install -r requirements.txt -r requirements-prod.txt; \
    else \
        pip install -r requirements.txt; \
    fi

# 再拷贝源码
COPY src ./src
COPY samples ./samples

ENV PYTHONPATH=/app/src
EXPOSE 8000

CMD ["python", "-m", "uvicorn", "nebula.api.server:app", "--host", "0.0.0.0", "--port", "8000"]
