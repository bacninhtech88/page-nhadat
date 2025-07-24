FROM python:3.10-slim

# Cài Rust để tránh lỗi maturin
RUN apt-get update && apt-get install -y \
    gcc \
    libffi-dev \
    build-essential \
    curl \
 && curl https://sh.rustup.rs -sSf | bash -s -- -y

ENV PATH="/root/.cargo/bin:$PATH"

# Tạo thư mục ứng dụng
WORKDIR /app

COPY . /app

# Cài pip và requirements
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Chạy ứng dụng FastAPI với uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
