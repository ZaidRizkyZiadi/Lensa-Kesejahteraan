import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app import server as app  # Flask WSGI milik Dash; Vercel mencari variabel `app`
