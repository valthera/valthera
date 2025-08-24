FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    OPENBLAS_CORETYPE=ARMV8 \
    OMP_NUM_THREADS=1 \
    OPENBLAS_NUM_THREADS=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg ca-certificates && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# CPU wheels + stable numpy to avoid illegal-instruction on linux/arm64
RUN pip install --upgrade pip && pip install \
  --extra-index-url https://download.pytorch.org/whl/cpu \
  torch==2.4.0 torchvision==0.19.0 torchaudio==2.4.0 \
  transformers==4.55.0 timm==1.0.7 einops==0.8.0 \
  numpy==1.26.4 opencv-python-headless==4.10.0.84

CMD ["bash"]
