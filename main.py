"""
Thin entrypoint so `uvicorn main:app --reload` works from the repo root.
The real app lives in `webpage-ai-parser/main.py`.
"""
import importlib.util
import sys
from pathlib import Path

_SUB = Path(__file__).resolve().parent / "webpage-ai-parser"
_sub_str = str(_SUB)
if _sub_str not in sys.path:
    sys.path.insert(0, _sub_str)

_spec = importlib.util.spec_from_file_location("webpage_ai_parser_main", _SUB / "main.py")
_module = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_module)
app = _module.app
