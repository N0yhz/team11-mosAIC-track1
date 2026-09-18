import os
import sys
from pathlib import Path

# Ensure backend directory is in sys.path for backward compatibility
_backend_dir = Path(__file__).resolve().parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

from app.core.config import settings

GOOGLE_API_KEY = settings.GOOGLE_API_KEY