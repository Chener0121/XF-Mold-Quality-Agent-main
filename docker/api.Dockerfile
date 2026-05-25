FROM python:3.12-slim

WORKDIR /app

# 安装 uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# 使用清华镜像加速
ENV UV_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple

# 先复制依赖文件以利用缓存
COPY pyproject.toml uv.lock ./

# 安装依赖
RUN uv sync --frozen --no-dev --no-install-project

# 复制后端源码
COPY backend/src ./backend/src

ENV PYTHONPATH=/app/backend

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
