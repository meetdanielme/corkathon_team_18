"""Copy Flask assets into Vercel's CDN-served public directory."""
import shutil
from pathlib import Path

root = Path(__file__).resolve().parents[1]
shutil.copytree(root / 'footfall/static', root / 'public/static', dirs_exist_ok=True)
