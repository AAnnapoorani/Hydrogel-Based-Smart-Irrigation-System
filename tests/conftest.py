import os
import sys

# Ensure backend directory is in PYTHONPATH for testing
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend"))
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
