"""Production entry point for Ultra KI V2 on Render."""
import importlib.util
from pathlib import Path

module_path = Path(__file__).with_name("Ultra KI V2 new.py")
spec = importlib.util.spec_from_file_location("ultra_ki_v2_app", module_path)
if spec is None or spec.loader is None:
    raise RuntimeError(f"Unable to load {module_path}")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
app = module.app

# Render-compatible health endpoint aliases.
app.add_url_rule("/api/health", endpoint="api_health", view_func=module.health)

if __name__ == "__main__":
    import os
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "10000")), debug=False)
