#!/usr/bin/env bash
set -Eeuo pipefail

model_root="${ACS_MODEL_ROOT:-/workspace/models}"
install_raw="${ACS_INSTALL_RAW:-1}"
base_url="https://huggingface.co/Comfy-Org/Krea-2/resolve/main"

mkdir -p \
  "$model_root/diffusion_models" \
  "$model_root/text_encoders" \
  "$model_root/vae" \
  "$model_root/loras" \
  "${ACS_LITE_DATA_DIR:-/workspace/acs-imagegen-lite-data}"

if [[ "${ACS_SKIP_MODEL_DOWNLOAD:-0}" == "1" ]]; then
  echo "Model download skipped by ACS_SKIP_MODEL_DOWNLOAD=1"
  exit 0
fi

verify_sha256() {
  local target="$1"
  local expected="$2"
  [[ -f "$target" ]] || return 1
  [[ "$(sha256sum "$target" | awk '{print $1}')" == "$expected" ]]
}

download_model() {
  local relative_path="$1"
  local expected="$2"
  local target="$model_root/$relative_path"
  local partial="$target.part"

  if verify_sha256 "$target" "$expected"; then
    echo "Verified: $relative_path"
    return 0
  fi
  if [[ -f "$target" ]]; then
    mv "$target" "$target.invalid.$(date +%Y%m%d%H%M%S)"
  fi

  echo "Downloading: $relative_path"
  curl --fail --location --retry 8 --retry-all-errors --continue-at - \
    --output "$partial" "$base_url/$relative_path"
  if ! verify_sha256 "$partial" "$expected"; then
    echo "SHA-256 verification failed: $relative_path" >&2
    return 1
  fi
  mv "$partial" "$target"
}

download_model \
  "diffusion_models/krea2_turbo_fp8_scaled.safetensors" \
  "eb4dd8c612cfd10f64f25b057e6e6bbcb5737c94a7372177e456dbf7579502f1"

if [[ "$install_raw" == "1" ]]; then
  download_model \
    "diffusion_models/krea2_raw_fp8_scaled.safetensors" \
    "48cd5d6c100297968349b41a8e77c6591d1dac18a215807f5f25f59e5c54cd61"
fi

download_model \
  "text_encoders/qwen3vl_4b_fp8_scaled.safetensors" \
  "54bd5144df0bbc25dd6ccadfcb826b521445a1b06ae5a42570bdd2974ca87094"
download_model \
  "vae/qwen_image_vae.safetensors" \
  "a70580f0213e67967ee9c95f05bb400e8fb08307e017a924bf3441223e023d1f"

echo "ACS ImageGen Lite models are ready."
