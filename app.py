"""Render/Gunicorn entry point for the legacy Ultra KI V2 module."""
import importlib.util
from pathlib import Path

module_path = Path(__file__).with_name("Ultra KI V2 new.py")
spec = importlib.util.spec_from_file_location("ultra_ki_v2_app", module_path)
if spec is None or spec.loader is None:
    raise RuntimeError(f"Unable to load {module_path}")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
app = module.app
