import os
from pathlib import Path

# Load .env from the project root (one level up from this package)
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError:
    pass

from .cli import main
main()
