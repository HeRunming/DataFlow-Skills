# Gotchas

## Common Failures

1. Missing registration decorator
- Symptom: operator not found in `OPERATOR_REGISTRY`
- Fix: add `@OPERATOR_REGISTRY.register()` and ensure module import path is reachable

2. Wrong storage lifecycle
- Symptom: operator reads empty data or writes unexpected step
- Fix: invoke with `storage.step()` from pipeline/CLI

3. Key mismatch
- Symptom: `KeyError` for input column
- Fix: validate `input_key` before processing and provide clear error message

4. LLM response shape assumptions
- Symptom: index error or empty output
- Fix: normalize return values (list/str/None) in a helper method

5. CLI/operator coupling
- Symptom: operator hard to test or reuse
- Fix: keep CLI-specific logic in separate module under `cli/`

6. Test brittleness
- Symptom: tests depend on external API
- Fix: use local dummy LLM classes and temporary files
