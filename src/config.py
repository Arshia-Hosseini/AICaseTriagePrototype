from pathlib import Path

OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_MODEL = "llama3.1:8b"
APP_TITLE = "AI Case Triage Prototype"
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

REFERENCE_DATA_FILE = DATA_DIR / "reference_data.json"
SAMPLE_CASES_FILE = DATA_DIR / "sample_cases.json"