"""Validator for i18n files against a simple schema.

Usage:
  python -m scripts.validate_translations

Exposed function for tests: validate_all() -> List[str]
"""
from __future__ import annotations

import importlib
import json
import pkgutil
import sys
from pathlib import Path
from typing import Dict, List, Tuple

I18N_PKG = "app.i18n"


def locate_schema_path() -> Path:
    """Locate strings_schema.json by searching parent directories.

    This makes the validator robust when imported from different package
    contexts (tests, installed package, etc.).
    """
    here = Path(__file__).resolve()
    for p in [here] + list(here.parents):
        candidate = p / "app" / "i18n" / "strings_schema.json"
        if candidate.exists():
            return candidate
    candidate = Path.cwd() / "app" / "i18n" / "strings_schema.json"
    if candidate.exists():
        return candidate
    raise FileNotFoundError("strings_schema.json not found; looked in parents and cwd")


SCHEMA_PATH = locate_schema_path()


def load_schema() -> List[str]:
    with SCHEMA_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return list(data.get("keys", []))


def find_i18n_modules() -> List[str]:
    pkg = importlib.import_module(I18N_PKG)
    modules = [m.name for m in pkgutil.iter_modules(pkg.__path__)]
    return modules


def load_strings_from_module(module_name: str) -> List[Tuple[str, Dict]]:
    """Return list of (variable_name, dict) for STRINGS_* vars in module."""
    full_name = f"{I18N_PKG}.{module_name}"
    mod = importlib.import_module(full_name)
    strings = []
    for attr in dir(mod):
        if attr.startswith("STRINGS_"):
            val = getattr(mod, attr)
            if isinstance(val, dict):
                strings.append((attr, val))
    return strings


def validate_all() -> List[str]:
    """Validate all i18n modules and return list of error messages (empty if OK)."""
    errors: List[str] = []
    schema_keys = set(load_schema())

    modules = find_i18n_modules()
    if not modules:
        errors.append("No i18n modules found under app.i18n")
        return errors

    for mod in modules:
        entries = load_strings_from_module(mod)
        if not entries:
            errors.append(f"Module app.i18n.{mod} has no STRINGS_* dict variable")
            continue
        for var_name, mapping in entries:
            # mapping is like { 'en': { ... } }
            if not isinstance(mapping, dict):
                errors.append(f"{mod}.{var_name} is not a dict")
                continue
            for lang_code, lang_map in mapping.items():
                if not isinstance(lang_map, dict):
                    errors.append(f"{mod}.{var_name}[{lang_code}] is not a dict")
                    continue
                found = set(lang_map.keys())
                missing = schema_keys - found
                extra = found - schema_keys
                if missing:
                    errors.append(
                        f"app.i18n.{mod}.{var_name}[{lang_code}] missing keys: {sorted(list(missing))}"
                    )
                # Warn about extra keys but not failing by default — include as info
                if extra:
                    errors.append(
                        f"app.i18n.{mod}.{var_name}[{lang_code}] has extra keys: {sorted(list(extra))}"
                    )
                # Type checks
                for k, v in lang_map.items():
                    if not isinstance(v, str):
                        errors.append(
                            f"app.i18n.{mod}.{var_name}[{lang_code}].{k} is not a string ({type(v).__name__})"
                        )
    return errors


def main() -> int:
    errs = validate_all()
    if not errs:
        print("i18n validation: OK")
        return 0
    print("i18n validation: FAILED", file=sys.stderr)
    for e in errs:
        print("-", e, file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())