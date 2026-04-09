from pathlib import Path

APP_TITLE = "AI Case Triage & Reassignment Prototype"

OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_MODEL = "llama3.1:8b"

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"

REFERENCE_DATA_FILE = DATA_DIR / "reference_data.json"
SAMPLE_CASES_FILE = DATA_DIR / "sample_cases.json"
TICKETS_FILE = DATA_DIR / "tickets.json"