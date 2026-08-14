#!/usr/bin/env bash
set -Eeuo pipefail

project_dir="/opt/acs-imagegen-lite"
model_root="${ACS_MODEL_ROOT:-/workspace/models}"
comfy_output="${ACS_COMFY_OUTPUT_DIR:-/workspace/comfy-output}"

auto_install="${ACS_AUTO_INSTALL_MODELS:-none}"
if [[ "$auto_install" == "all" ]]; then
  ACS_INSTALL_RAW=1 "$project_dir/scripts/bootstrap.sh"
elif [[ "$auto_install" == "turbo" ]]; then
  ACS_INSTALL_RAW=0 "$project_dir/scripts/bootstrap.sh"
else
  echo "Model installation will be handled from the Lite UI."
fi
mkdir -p "$comfy_output" /workspace/comfy-input

python /opt/ComfyUI/main.py \
  --listen 127.0.0.1 \
  --port 8188 \
  --output-directory "$comfy_output" \
  --input-directory /workspace/comfy-input \
  --extra-model-paths-config <(printf 'acs_imagegen_lite:\n  base_path: %s\n  diffusion_models: diffusion_models\n  text_encoders: text_encoders\n  vae: vae\n  loras: loras\n' "$model_root") &
comfy_pid=$!

python "$project_dir/scripts/watchdog.py" &
watchdog_pid=$!

cleanup() {
  kill "$watchdog_pid" "$comfy_pid" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

exec python -m uvicorn app.server:app --host 0.0.0.0 --port 8080 --proxy-headers --forwarded-allow-ips='*'
