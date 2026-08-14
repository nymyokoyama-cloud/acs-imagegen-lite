FROM runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404

ARG COMFYUI_COMMIT=4800e78518ebb1f2a9443ea5418edbff6c3935f9

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    ACS_LITE_DATA_DIR=/workspace/acs-imagegen-lite-data \
    ACS_MODEL_ROOT=/workspace/models \
    ACS_COMFY_OUTPUT_DIR=/workspace/comfy-output

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl git \
    && rm -rf /var/lib/apt/lists/*

RUN git clone https://github.com/comfyanonymous/ComfyUI.git /opt/ComfyUI \
    && git -C /opt/ComfyUI checkout "$COMFYUI_COMMIT"

COPY requirements.txt /opt/acs-imagegen-lite/requirements.txt
RUN python -m pip install --no-cache-dir -r /opt/ComfyUI/requirements.txt \
    && python -m pip install --no-cache-dir -r /opt/acs-imagegen-lite/requirements.txt

COPY app /opt/acs-imagegen-lite/app
COPY scripts /opt/acs-imagegen-lite/scripts
RUN chmod 0755 /opt/acs-imagegen-lite/scripts/bootstrap.sh /opt/acs-imagegen-lite/scripts/start.sh

WORKDIR /opt/acs-imagegen-lite
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=5 \
    CMD curl --fail http://127.0.0.1:8080/healthz || exit 1
CMD ["/opt/acs-imagegen-lite/scripts/start.sh"]
