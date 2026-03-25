# DataFlow Operator Contract

## Core Interface

All generated operators must follow this baseline:

```python
@OPERATOR_REGISTRY.register()
class XxxOperator(OperatorABC):
    @staticmethod
    def get_desc(lang: str = "zh") -> str:
        ...

    def run(self, storage: DataFlowStorage, ...) -> str | None:
        ...
```

## Required Behavior

- `run` reads from `storage.read("dataframe")`
- `run` validates required input columns
- `run` writes back with `storage.write(dataframe)`
- `run` returns the output key (or `None` for dataset-level eval)

## Data Contract

- Input and output should be column-based transformation on a DataFrame
- Avoid tightly coupling operator internals with CLI interaction
- Keep deterministic behavior when LLM is disabled

## Description Contract

`get_desc` should include:
- Chinese version (`lang="zh"`)
- English version (`lang="en"`)
- A fallback short string for unknown language code
