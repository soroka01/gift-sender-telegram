from types import ModuleType
from typing import Any


def config_value(module: ModuleType, name: str, default: Any = None) -> Any:
    """Read a scalar config value and tolerate an accidental trailing comma."""
    value = getattr(module, name, default)
    if isinstance(value, tuple):
        if len(value) != 1:
            raise RuntimeError(f"{name} in config.py must contain exactly one value.")
        return value[0]
    return value
