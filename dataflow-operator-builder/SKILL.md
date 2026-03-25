---
name: dataflow-operator-builder
description: Builds production-grade DataFlow operator scaffolds (generate/filter/refine/eval) for Codex and general coding agents. Use when user asks to create a new DataFlow operator, scaffold operator templates, add OPERATOR_REGISTRY registration, add DataFlowStorage-based CLI wrappers, or generate operator test suites.
version: 1.0.0
---

# DataFlow Operator Builder

Generate production-ready DataFlow operator artifacts with a fixed two-round interview workflow.

## Usage

```bash
/dataflow-operator-builder
/dataflow-operator-builder --spec path/to/spec.json --output-root path/to/repo
/dataflow-operator-builder --dry-run --spec path/to/spec.json --output-root path/to/repo
```

## Script Directory

**Agent Execution Instructions**:
1. Determine this `SKILL.md` directory as `SKILL_DIR`
2. Use script path `${SKILL_DIR}/scripts/build_operator_artifacts.py`

| Script | Purpose |
|--------|---------|
| `scripts/build_operator_artifacts.py` | Instantiate operator + CLI + tests from interview spec |
| `scripts/example_spec.json` | Reference input spec |

## Scope

This skill targets:
- DataFlow main-repo coding style
- `DataFlowStorage`-based operator implementation
- `OPERATOR_REGISTRY.register()` registration
- Separate CLI wrapper file for human-in-the-loop usage
- Minimal but production-grade test skeleton

Default operator families:
- `generate`
- `filter`
- `refine`
- `eval`

## Two-Round Interview (Required)

Use **AskUserQuestion** in **batch mode** for each round. Do not ask one-by-one.

### Round 1 (Structure)

Ask in one batch:
1. Operator family (`generate/filter/refine/eval`)
2. Class name + output module file name
3. Package name + output root path
4. Whether LLM dependency is needed
5. CLI module name

### Round 2 (Implementation details)

Ask in one batch:
1. `input_key` and `output_key`
2. Chinese/English operator description preference
3. Extra CLI args (if any)
4. Test file prefix
5. Overwrite strategy (`overwrite-all/skip-existing/ask-each`)

Interview schemas and recommended options:
- `references/askuserquestion-rounds.md`

## Workflow

Copy this checklist and check off while executing:

```text
Operator Builder Progress:
- [ ] Step 1: Load references
- [ ] Step 2: Round 1 AskUserQuestion (batch)
- [ ] Step 3: Round 2 AskUserQuestion (batch)
- [ ] Step 4: Build JSON spec
- [ ] Step 5: Dry-run file plan
- [ ] Step 6: Confirm overwrite policy (light guardrail)
- [ ] Step 7: Generate files
- [ ] Step 8: Quick validation
- [ ] Step 9: Report generated artifacts
```

### Step 1: Load References

Read:
- `references/operator-contract.md`
- `references/registration-rules.md`
- `references/cli-shell-guidelines.md`
- `references/gotchas.md`

### Step 2-3: Interview with AskUserQuestion

Strictly follow `references/askuserquestion-rounds.md`.

### Step 4: Build Spec JSON

Create a spec file using:
- `scripts/example_spec.json`

### Step 5: Dry-Run

Run:

```bash
python "${SKILL_DIR}/scripts/build_operator_artifacts.py" \
  --spec <spec.json> \
  --output-root <repo-root> \
  --dry-run
```

### Step 6: Light Guardrail (Required)

Before writing files, show:
- Full file creation/update list
- Which files already exist
- Selected overwrite policy

Then ask for explicit confirmation (`y/N`).

### Step 7: Generate

Run without `--dry-run`:

```bash
python "${SKILL_DIR}/scripts/build_operator_artifacts.py" \
  --spec <spec.json> \
  --output-root <repo-root>
```

### Step 8: Quick Validation

- Ensure generated operator imports successfully
- Ensure class is decorated with `@OPERATOR_REGISTRY.register()`
- Ensure tests are generated in `test/`

### Step 9: Output Summary

Report:
- Operator class
- Paths generated/updated
- Overwrite behavior
- Suggested next test commands

## File Layout Produced by Script

```text
<output-root>/
├── <package_name>/
│   ├── __init__.py
│   ├── cli/
│   │   └── <cli_module_name>.py
│   └── operators/
│       ├── __init__.py
│       └── <operator_type>/
│           ├── __init__.py
│           └── <operator_module_name>.py
└── test/
    ├── test_<prefix>_unit.py
    ├── test_<prefix>_registry.py
    └── test_<prefix>_smoke.py
```

## Notes

- This skill does not maintain runtime memory logs.
- This skill uses light guardrails, not strict blocking.
- Prefer behavior-level customization after scaffold generation.
