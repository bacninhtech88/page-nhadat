FROM python:3.11-slim

# Cài Rust (dùng rustup)
RUN apt-get update && apt-get install -y curl gcc build-essential libssl-dev \
    && curl https://sh.rustup.rs -sSf | sh -s -- -y \
    && . "$HOME/.cargo/env"

# Set env để maturin và cargo hoạt động
ENV PATH="/root/.cargo/bin:$PATH"

# Tạo thư mục app
WORKDIR /app

# Copy file requirements trước (để tận dụng cache)
COPY requirements.txt .

# Cài các dependencies Python, kể cả những cái cần Rust (chromadb, pydantic-core, ...)
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ source code vào container
COPY . .

# Chạy app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
