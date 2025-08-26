# /app/sitecustomize.py
# Sorgt dafür, dass sowohl "from app...." als auch "from modules|services ..." funktionieren.
import os, sys

BASE_DIR = os.path.abspath(os.path.dirname(__file__))     # /app
PKG_DIR  = os.path.join(BASE_DIR, "app")                  # /app/app

# /app auf sys.path (für "import app")
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# /app/app auf sys.path (damit "import modules" / "import services" geht)
if PKG_DIR not in sys.path:
    sys.path.insert(0, PKG_DIR)
