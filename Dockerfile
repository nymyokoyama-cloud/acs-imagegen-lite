FROM nvidia/cuda:12.8.1-cudnn-runtime-ubuntu24.04@sha256:9175fa92f96de35a8cfb9493f0dfcf9435c7a597e9d95ad41d2cae382a95e3f9

ARG COMFYUI_COMMIT=7fe8a6138504f90ff7be82f3babf416da32876b1

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH=/opt/venv/bin:$PATH \
    HF_XET_HIGH_PERFORMANCE=1 \
    HF_HUB_DISABLE_PROGRESS_BARS=1 \
    ACS_LITE_DATA_DIR=/workspace/acs-imagegen-lite-data \
    ACS_MODEL_ROOT=/workspace/models \
    ACS_COMFY_OUTPUT_DIR=/workspace/comfy-output \
    ACS_COMFY_INPUT_DIR=/workspace/comfy-input

RUN apt-get update \
    && apt-get upgrade -y --no-install-recommends \
    && apt-get install -y --no-install-recommends ca-certificates curl ffmpeg git python3 python3-venv \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/venv \
    && python -m pip install --no-cache-dir --upgrade pip setuptools wheel \
    && python -m pip install --no-cache-dir \
        torch==2.8.0 torchvision==0.23.0 torchaudio==2.8.0 \
        --index-url https://download.pytorch.org/whl/cu128

RUN git clone https://github.com/Comfy-Org/ComfyUI.git /opt/ComfyUI \
    && git -C /opt/ComfyUI checkout "$COMFYUI_COMMIT"

COPY requirements.txt /opt/acs-imagegen-lite/requirements.txt
RUN python -m pip install --no-cache-dir -r /opt/ComfyUI/requirements.txt \
    && python -m pip install --no-cache-dir -r /opt/acs-imagegen-lite/requirements.txt

COPY app /opt/acs-imagegen-lite/app
COPY scripts /opt/acs-imagegen-lite/scripts
COPY KREA2_NOTICE.txt MINIMAX_H3_LICENSE.txt MINIMAX_H3_NOTICE.txt THIRD_PARTY_NOTICES.md /opt/acs-imagegen-lite/
COPY docs/KREA2-TERMS.md docs/H3-TERMS.md docs/H3-ENFORCEMENT.md /opt/acs-imagegen-lite/docs/
RUN chmod 0755 /opt/acs-imagegen-lite/scripts/bootstrap.sh /opt/acs-imagegen-lite/scripts/start.sh

WORKDIR /opt/acs-imagegen-lite
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=5 \
    CMD curl --fail http://127.0.0.1:8080/healthz || exit 1
CMD ["/opt/acs-imagegen-lite/scripts/start.sh"]
