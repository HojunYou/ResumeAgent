"""
utils/ollama_utils.py
=====================

Starts (or re-uses) a local `ollama serve` process on macOS and guarantees that
the REST endpoint is alive **before** any agent code proceeds.

Importing this module once is enough:

    import utils.ollama_utils        # side-effect: ensure_ollama_running()

Public API
----------
ensure_ollama_running(max_wait: int = 15) -> bool
"""

from __future__ import annotations
import os, shutil, subprocess, time, requests, platform, logging, sys

# Allow user overrides
OLLAMA_BIN  = os.getenv("OLLAMA_BIN", "ollama")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
LOGGER      = logging.getLogger("ollama_utils")

# --------------------------------------------------------------------------- #
#                                helpers                                      #
# --------------------------------------------------------------------------- #
def _is_endpoint_up() -> bool:
    try:
        r = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=2)
        return r.status_code == 200
    except requests.RequestException:
        return False


def _proc_exists() -> bool:
    """macOS-native: `pgrep -f 'ollama.*serve'` → True/False."""
    return (
        subprocess.call(
            ["pgrep", "-f", r"ollama.*serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        == 0
    )


def _launch_detached() -> bool:
    """Spawn `ollama serve` in its own session so it survives parent exit."""
    if shutil.which(OLLAMA_BIN) is None:
        LOGGER.error("ollama binary not found on PATH.")
        return False

    try:
        subprocess.Popen(
            [OLLAMA_BIN, "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,          # keeps it alive after parent exits
        )
        return True
    except Exception as exc:                # noqa: BLE001
        LOGGER.error("Could not launch ollama: %s", exc)
        return False


# --------------------------------------------------------------------------- #
#                            public function                                  #
# --------------------------------------------------------------------------- #
def ensure_ollama_running(max_wait: int = 15) -> bool:
    """
    Make sure Ollama is listening on OLLAMA_HOST.

    Returns
    -------
    bool
        True if running; False otherwise.
    """
    if _is_endpoint_up():
        return True

    LOGGER.info("Ollama not detected; launching …")
    if _proc_exists() or _launch_detached():
        # Poll until the HTTP endpoint responds
        deadline = time.time() + max_wait
        while time.time() < deadline:
            if _is_endpoint_up():
                LOGGER.info("Ollama is ready.")
                return True
            time.sleep(1)

    LOGGER.error("Timed out waiting for Ollama.")
    return False


# --------------------------------------------------------------------------- #
#           run once at import so *all* agents inherit the guarantee          #
# --------------------------------------------------------------------------- #
if platform.system() == "Darwin":           # macOS only; skip on CI Linux etc.
    if not ensure_ollama_running():
        LOGGER.critical("Ollama unavailable – exiting.")
        sys.exit(1)