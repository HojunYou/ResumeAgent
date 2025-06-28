import os, time, shutil, subprocess, requests

# Allow overrides:
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_BIN  = os.getenv("OLLAMA_BIN", "ollama")        # e.g. /opt/homebrew/bin/ollama

def is_ollama_running(host: str = OLLAMA_HOST) -> bool:
    """Ping the Ollama REST endpoint."""
    try:
        return requests.get(f"{host}/api/tags", timeout=2).status_code == 200
    except requests.RequestException:
        return False

def _ollama_process_exists() -> bool:
    """Use macOS pgrep to see if 'ollama serve' is already running."""
    return subprocess.call(
        ["pgrep", "-f", r"ollama.*serve"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ) == 0

def launch_ollama() -> bool:
    """Start `ollama serve` in the background (detached)."""
    if _ollama_process_exists():
        return True

    if shutil.which(OLLAMA_BIN) is None:
        print("[Error] The 'ollama' executable is not in PATH.")
        return False

    try:
        subprocess.Popen(
            [OLLAMA_BIN, "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,        # <-- key for macOS: create its own session
        )
        return True
    except Exception as exc:
        print(f"[Error] Could not launch Ollama: {exc}")
        return False

def ensure_ollama_running(max_wait: int = 15) -> bool:
    """Guarantee that a local Ollama server is listening."""
    if is_ollama_running():
        return True

    print("[Info] Ollama not detected; launching …")
    if not launch_ollama():
        return False

    deadline = time.time() + max_wait
    while time.time() < deadline:
        if is_ollama_running():
            print("[Info] Ollama is ready.")
            return True
        time.sleep(1)

    print("[Error] Timed out waiting for Ollama to start.")
    return False