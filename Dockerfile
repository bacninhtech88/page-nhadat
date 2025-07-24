# Base image dùng Python chính thức
FROM python:3.11-slim

# Cài trình biên dịch Rust để hỗ trợ maturin nếu cần
RUN apt-get update && apt-get install -y curl build-essential git libffi-dev \
    && curl https://sh.rustup.rs -sSf | sh -s -- -y \
    && . "$HOME/.cargo/env"

# Tạo thư mục ứng dụng
WORKDIR /app

# Copy toàn bộ mã nguồn
COPY . .

# Cài thư viện Python
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# Chạy app FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
