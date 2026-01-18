"""
Shared utilities and configuration constants.
"""
import os
from pathlib import Path

# Paths
PROJECT_ROOT = os.getcwd()
CONFIG_DIR = os.path.join(PROJECT_ROOT, "config")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")
LOG_DIR = os.path.join(PROJECT_ROOT, "logs")
DB_PATH = os.path.join(PROJECT_ROOT, "data.sqlite")
LOCK_PATH = os.path.join(PROJECT_ROOT, "run.lock")
KEYWORDS_PATH = os.path.join(CONFIG_DIR, "keywords.txt")

# Create directories if needed
for directory in [CONFIG_DIR, OUTPUT_DIR, LOG_DIR]:
    os.makedirs(directory, exist_ok=True)

# Default values
DEFAULT_OUTPUT_FILE = os.path.join(OUTPUT_DIR, "results.json")
DEFAULT_RATE_LIMIT = 2
DEFAULT_PAGE_SIZE = 20
DEFAULT_MAX_PAGES = 50

# HTTP settings
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.bilibili.com",
    "Accept": "application/json, text/javascript, */*; q=0.01",
}

# Exit codes
EXIT_SUCCESS = 0
EXIT_ALREADY_RUNNING = 4
EXIT_PERMANENT_ERROR = 2
EXIT_TRANSIENT_ERROR = 1
