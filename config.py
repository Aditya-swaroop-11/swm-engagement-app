"""Settings. Everything can be overridden from the .env file (see .env.example)."""
import os
from pathlib import Path

BASE = Path(__file__).resolve().parent


def _load_env():
    f = BASE / ".env"
    if f.exists():
        for line in f.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


_load_env()

DATA_DIR = Path(os.environ.get("DATA_DIR", BASE / "data"))
PDF_DIR = DATA_DIR / "agreements"
OUTBOX_DIR = DATA_DIR / "outbox"          # emails are saved here when SMTP is not configured
EXCEL_PATH = DATA_DIR / "Associates_Register.xlsx"
COUNTER_PATH = DATA_DIR / "id_counter.json"

ID_PREFIX = os.environ.get("ID_PREFIX", "SWM/TTL/2026/")
ID_START = int(os.environ.get("ID_START", "21078"))

# Compensation split of the monthly gross figure
SPLIT = (("Base Retainer Pay", 44.8), ("Operational & Field Logistics", 20.0), ("Performance Deliverable Pay", 35.2))

SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "hr@smartworkmart.com")
SENDER_NAME = os.environ.get("SENDER_NAME", "Smart Work Mart HR")
SMTP_HOST = os.environ.get("SMTP_HOST", "")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", SENDER_EMAIL)
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
SMTP_SECURITY = os.environ.get("SMTP_SECURITY", "starttls").lower()   # starttls | ssl

# --- Live Google Sheet (cloud Excel). Leave SHEET_WEBHOOK_URL empty to use the local Excel file instead. ---
SHEET_WEBHOOK_URL = os.environ.get("SHEET_WEBHOOK_URL", "")
SHEET_SECRET = os.environ.get("SHEET_SECRET", "")
SHEET_URL = os.environ.get("SHEET_URL", "")          # the link the client opens to see the live sheet

# --- Login for the web page (strongly recommended when it is on the internet) ---
APP_USERNAME = os.environ.get("APP_USERNAME", "hr")
APP_PASSWORD = os.environ.get("APP_PASSWORD", "")

ONBOARDING_FORM_URL = os.environ.get("ONBOARDING_FORM_URL", "https://forms.gle/bvg44gZmw4HT8JyK6")
ROLES = ["Field Sales Associate", "Operation Leader"]
ENGAGEMENT_TYPE = "Commercial Field Service"
