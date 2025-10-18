# ------------------------------------------
# ✅ DGX Spark / ARM64 NVIDIA PyTorch 2.9 + TorchVision (source build)
# ------------------------------------------

FROM nvcr.io/nvidia/pytorch:24.09-py3 AS base
FROM base AS final

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    FORCE_CUDA=1

# -----------------------------
# 🧱 System dependencies
# -----------------------------
RUN apt-get update && apt-get install -y \
    build-essential cmake git wget curl vim ffmpeg ninja-build \
    libjpeg-dev zlib1g-dev libavcodec-dev libavformat-dev libavfilter-dev \
    libavutil-dev libswresample-dev libswscale-dev libsm6 libxext6 python3-dev && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# -----------------------------
# 🎥 Build and install Decord (with CUDA, skip NVDEC)
# -----------------------------
WORKDIR /tmp/decord-build
RUN git clone --recursive https://github.com/dmlc/decord.git && \
    cd decord && \
    sed -i '/cmake\/modules\/CUDA\.cmake/d' CMakeLists.txt && \
    mkdir -p cmake/modules && echo "# stubbed CUDA.cmake" > cmake/modules/CUDA.cmake && \
    mkdir build && cd build && \
    cmake .. -DUSE_CUDA=ON -DUSE_NVDEC=OFF -DCMAKE_BUILD_TYPE=Release && \
    make -j"$(nproc)" && \
    cd ../python && USE_CUDA=1 USE_NVDEC=0 python3 setup.py install && \
    cd / && rm -rf /tmp/decord-build

# -----------------------------
# 📦 Core Python dependencies
# -----------------------------
RUN pip install --upgrade pip setuptools wheel && \
    pip install "numpy<2" "pandas<2.2.3" "pyarrow<16.2.0" && \
    pip install transformers accelerate timm einops ffmpeg-python opencv-python-headless tqdm matplotlib

# -----------------------------
# 🔥 Install PyTorch 2.9.0 (CUDA 12.8 / ARM64)
# -----------------------------
RUN pip uninstall -y torch torchvision torch-tensorrt || true && \
    pip install torch==2.9.0+cu128 --extra-index-url https://download.pytorch.org/whl/cu128 && \
    python3 -c "import torch; print('✅ Installed Torch', torch.__version__, '| CUDA', torch.version.cuda)"

# -----------------------------
# 🧩 Build TorchVision from source (matching Torch 2.9)
# -----------------------------
WORKDIR /tmp/torchvision
RUN git clone --branch main https://github.com/pytorch/vision.git . && \
    python3 setup.py install && \
    cd / && rm -rf /tmp/torchvision

# -----------------------------
# 🧹 Cleanup
# -----------------------------
RUN apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# -----------------------------
# 🧠 Runtime GPU check script
# -----------------------------
RUN echo 'import torch, torchvision; \
print(f"Torch {torch.__version__}, CUDA {torch.version.cuda}, TV {torchvision.__version__}"); \
print("GPU available:", torch.cuda.is_available()); \
print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else "No GPU detected.")' \
> /usr/local/bin/check_torch.py

# -----------------------------
# 🧰 Workspace
# -----------------------------
WORKDIR /workspace
ENTRYPOINT ["/bin/bash"]
