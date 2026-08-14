from __future__ import annotations

import os
import tempfile
from pathlib import Path


TEST_ROOT = Path(tempfile.mkdtemp(prefix="acs-imagegen-lite-tests-"))
os.environ["ACS_LITE_DATA_DIR"] = str(TEST_ROOT / "data")
os.environ["ACS_MODEL_ROOT"] = str(TEST_ROOT / "models")
os.environ["ACS_COMFY_INPUT_DIR"] = str(TEST_ROOT / "comfy-input")
os.environ["ACS_LITE_DISABLE_WORKER"] = "1"
os.environ["ACS_LITE_DISABLE_MODEL_DOWNLOAD"] = "1"
os.environ["ACS_COOKIE_SECURE"] = "0"
os.environ["RUNPOD_DC_ID"] = "AP-JP-1"
