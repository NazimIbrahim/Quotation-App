"""
Main entry point for AMA Ceramics Quotation Management System.
"""
import sys
import ctypes
from pathlib import Path

# Add project root to Python module search path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import os

# Redirect stdout / stderr if None (prevents crashes under --noconsole on Windows)
if sys.stdout is None:
    try:
        sys.stdout = open(os.devnull, "w", encoding="utf-8")
    except Exception:
        pass
if sys.stderr is None:
    try:
        sys.stderr = open(os.devnull, "w", encoding="utf-8")
    except Exception:
        pass

if hasattr(sys.stdout, 'reconfigure') and sys.stdout is not None:
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Enable High-DPI awareness on Windows for crisp rendering
if sys.platform.startswith("win"):
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

from app.database.models import init_database
from app.database.seed_data import seed_database
from app.ui.app_window import AppWindow


def main():
    print("=" * 65)
    print("  ✦ AMA CERAMICS PVT LTD - QUOTATION MANAGEMENT SYSTEM")
    print("=" * 65)
    print("Initializing SQLite Database and schema...")
    init_database()
    
    print("Checking seed demo data...")
    seed_database(force=False)
    
    print("Launching Desktop Application GUI...")
    app = AppWindow()
    app.mainloop()
    print("Application closed.")


if __name__ == "__main__":
    main()
