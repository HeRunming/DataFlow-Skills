# Registration Rules

## Registry Requirement

Each operator class must be decorated:

```python
@OPERATOR_REGISTRY.register()
```

Use imports:

```python
from dataflow.utils.registry import OPERATOR_REGISTRY
from dataflow.core import OperatorABC
```

## Package Import Rule

To make registration effective after import:
- package-level `__init__.py` should auto-import operator modules, or
- tests/import paths should directly import operator module

Preferred pattern:
- Keep an auto importer in `<package_name>/__init__.py`
- Keep `operators/<type>/__init__.py` explicit and simple

## Test Rule

Registration test must validate:
- class name appears in `OPERATOR_REGISTRY`
- `OPERATOR_REGISTRY.get(class_name)` resolves to the class
