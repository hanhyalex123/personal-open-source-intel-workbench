import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"


def load_environment() -> None:
    load_dotenv()
    apply_runtime_network_defaults()


def apply_runtime_network_defaults() -> None:
    # The backend talks to public endpoints directly. Ignore user-local proxy
    # variables from .env to avoid breaking TLS against local proxy listeners.
    os.environ["NO_PROXY"] = "*"
    os.environ["no_proxy"] = "*"
