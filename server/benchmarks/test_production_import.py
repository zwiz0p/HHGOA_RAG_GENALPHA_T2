import os
import sys
import gc
import psutil

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

def get_rss():
    gc.collect()
    return psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)

print(f"1. Base Python RSS: {get_rss():.2f} MB")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import production FastAPI app
import app.main
print(f"2. After importing app.main RSS: {get_rss():.2f} MB")

# Inspect sys.modules
has_torch = "torch" in sys.modules
has_st = "sentence_transformers" in sys.modules

print("\n==================================================")
print("PRODUCTION APPLICATION IMPORT AUDIT:")
print(f"  PyTorch ('torch') imported in sys.modules:              {has_torch}")
print(f"  SentenceTransformers ('sentence_transformers') imported: {has_st}")
print(f"  Total loaded modules in sys.modules:                   {len(sys.modules)}")
print("==================================================")
