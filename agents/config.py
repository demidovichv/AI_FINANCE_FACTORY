from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = PROJECT_ROOT / "data"

OFFERS_DIR = DATA_DIR / "Offers"

ARTICLES_DIR = DATA_DIR / "Articles"
ARTICLES_DRAFTS_DIR = ARTICLES_DIR / "drafts"
ARTICLES_HTML_DIR = ARTICLES_DIR / "html"

PIPELINE_STATUS_DIR = DATA_DIR / "Pipeline_Status"

LOGS_DIR = DATA_DIR / "Logs"

LOCKS_DIR = PROJECT_ROOT / ".locks"