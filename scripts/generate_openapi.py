"""Generate OpenAPI schema files (JSON and optionally YAML).

Usage:
    python scripts/generate_openapi.py

This will write files to ./openapi/openapi.json and ./openapi/openapi.yaml (if PyYAML installed).
"""
from pathlib import Path
import json

from app.main import app

OUT_DIR = Path("openapi")
OUT_DIR.mkdir(exist_ok=True)

schema = app.openapi()
json_path = OUT_DIR / "openapi.json"
with json_path.open("w", encoding="utf-8") as f:
    json.dump(schema, f, ensure_ascii=False, indent=2)
print(f"Wrote OpenAPI JSON to {json_path}")

try:
    import yaml

    yaml_path = OUT_DIR / "openapi.yaml"
    with yaml_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(schema, f, sort_keys=False, allow_unicode=True)
    print(f"Wrote OpenAPI YAML to {yaml_path}")
except Exception:
    print("PyYAML not installed; skipping YAML output. Install with `pip install pyyaml` to enable YAML export.")

print("Schema title:", schema.get("info", {}).get("title"))
print("Schema version:", schema.get("info", {}).get("version"))
print("Available paths:")
for p in sorted(schema.get("paths", {}).keys()):
    print(" -", p)
