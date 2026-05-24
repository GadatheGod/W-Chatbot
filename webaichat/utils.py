import logging
import os
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("webaichat")

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)
CHROMA_DIR = os.path.join(DATA_DIR, "chroma")
CONVS_DIR = os.path.join(DATA_DIR, "conversations")
DB_PATH = os.path.join(DATA_DIR, "webaichat.db")
LOGS_DIR = os.path.join(DATA_DIR, "logs")

os.makedirs(CHROMA_DIR, exist_ok=True)
os.makedirs(CONVS_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)
