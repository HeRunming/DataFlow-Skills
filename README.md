# DataFlow-Skills

Reusable agent skills for DataFlow workflows.

中文文档: [README_zh.md](./README_zh.md)

---

## `generating-dataflow-pipeline`
video tutorial: [Generate DataFlow Pipeline](https://github.com/user-attachments/assets/ca1fefbf-9bf7-469f-b856-b201952fb99b)

Reasoning-guided pipeline planner that generates standard DataFlow pipeline code from a task description and sample data.

### What It Does

Given a **target** (what the pipeline should achieve) and a **sample JSONL file** (1-5 representative rows), this skill:

1. Reads and analyzes the sample data — infers field types, content characteristics, and task nature
2. Selects operators from six core primitives (with extended operators available when needed) using a mandatory decision table
3. Validates field dependencies across the operator chain
4. Outputs a two-stage result: an intermediate operator decision (JSON) followed by a complete, runnable Python pipeline

### Quick Start

#### 1. Install Claude Code

Install [Claude Code](https://claude.ai/code) via any of the following:

- **CLI**: `npm install -g @anthropic-ai/claude-code`
- **Desktop app**: Available for Mac and Windows
- **IDE extensions**: Supports VSCode, etc.

#### 2. Add the Skill

Clone this repository and copy the skill directories into your Claude Code skills folder:

```bash
git clone https://github.com/haolpku/DataFlow-Skills.git

# Project-level (this project only)
cp -r DataFlow-Skills/generating-dataflow-pipeline .claude/skills/generating-dataflow-pipeline
cp -r DataFlow-Skills/core_text .claude/skills/core_text

# Or personal-level (all your projects)
cp -r DataFlow-Skills/generating-dataflow-pipeline ~/.claude/skills/generating-dataflow-pipeline
cp -r DataFlow-Skills/core_text ~/.claude/skills/core_text
```

Claude Code discovers skills from `.claude/skills/<skill-name>/SKILL.md`. The `name` field in `SKILL.md` frontmatter becomes the `/slash-command`. For more details, see the [official skills documentation](https://code.claude.com/docs/en/skills).

#### 3. Prepare Your Data

Create a JSONL file (one JSON object per line) with 1–5 representative rows:

```jsonl
{"product_name": "Laptop", "category": "Electronics"}
{"product_name": "Coffee Maker", "category": "Appliances"}
```

#### 4. Run the Skill

In Claude Code, invoke `/generating-dataflow-pipeline` and describe your target:

```
/generating-dataflow-pipeline
Target: Generate product descriptions and filter high-quality ones
Sample file: ./data/products.jsonl
Expected outputs: generated_description, quality_score
```

#### 5. Review the Output

The skill returns a two-stage result:

1. **Intermediate Operator Decision** — JSON with operator chain, field flow, and reasoning
2. **Field Mapping** — which fields exist vs. need to be generated
3. **Ordered Operator List** — operators in execution order with justification
4. **Reasoning Summary** — why this design satisfies the target
5. **Complete Pipeline Code** — full executable Python following standard structure
6. **Adjustable Parameters / Caveats** — tunable knobs and debugging tips

### Six Core Operators

| Operator | Purpose | LLM? |
|----------|---------|------|
| `PromptedGenerator` | Single-field LLM generation | Yes |
| `FormatStrPromptedGenerator` | Multi-field template-based generation | Yes |
| `Text2MultiHopQAGenerator` | Multi-hop QA pair construction from text | Yes |
| `PromptedFilter` | LLM-based quality scoring & filtering | Yes |
| `GeneralFilter` | Rule-based deterministic filtering | No |
| **KBC Trio** (3 operators, always together in order) | File/URL -> Markdown -> chunks -> clean text | Partial |

### Generated Pipeline Structure

All generated pipelines follow the same standard structure:

```python
from dataflow.operators.core_text import PromptedGenerator, PromptedFilter
from dataflow.serving import APILLMServing_request
from dataflow.utils.storage import FileStorage

class MyPipeline:
    def __init__(self):
        self.storage = FileStorage(
            first_entry_file_name="./data/input.jsonl",  # User-provided path
            cache_path="./cache",
            file_name_prefix="step",
            cache_type="jsonl"
        )
        self.llm_serving = APILLMServing_request(
            api_url="https://api.openai.com/v1/chat/completions",
            model_name="gpt-4o",
            max_workers=10
        )
        # Operator instances ...

    def forward(self):
        # Sequential operator.run() calls, each with storage.step()
        ...

if __name__ == "__main__":
    pipeline = MyPipeline()
    pipeline.forward()
```

Key rules:
- `first_entry_file_name` is set to the exact user-provided JSONL path
- Each `operator.run()` call uses `storage=self.storage.step()` for checkpointing
- Fields propagate forward: a field must exist in the sample or be output by a prior step before it can be consumed

### Extended Operators

Beyond the 6 core primitives, DataFlow provides additional operators. See the [`core_text`](#core_text) section for the full operator reference.

### Adding a New Operator

Prerequisite: the new operator's skill definition already exists (with `SKILL.md`, `examples/good.md`, `examples/bad.md`, etc.).

#### As an Extended Operator

Two steps are required:

**Step 1.** Create an operator directory with its skill definition under any appropriate location (e.g., `core_text/<category>/`, or a separate skill package):

```
<skill-directory>/<your-operator-name>/
├── SKILL.md          # API reference (constructor, run() signature, execution logic, constraints)
├── SKILL_zh.md       # Chinese translation (optional)
└── examples/
    ├── good.md       # Best-practice example
    └── bad.md        # Common mistakes
```

**Step 2.** Register the operator in `SKILL.md`'s **Extended Operator Reference** section. Add a row to the corresponding category table (Generate / Filter / Refine / Eval) with the operator name, subdirectory path, and description. Without this entry, the pipeline generator will not know the operator exists.

#### Promoting to a Core Primitive (Optional)

If the operator is used frequently enough to warrant priority selection, promote it by modifying `SKILL.md`:

1. **Preferred Operator Strategy** — Add to the core primitives list
2. **Operator Selection Priority Rule** — Add a decision table row (when to use / when not to use)
3. **Operator Parameter Signature Rule** — Add full constructor and `run()` signatures
4. **Correct Import Paths** — Add the import path
5. **Input File Content Analysis Rule** — Add input pattern matching if it handles a new data type
6. **Extended Operator Reference** — Update or remove the entry from the extended table to avoid duplication with core primitives
7. **Examples** — Add a complete example in `examples/` (recommended)

---

## `core_text`

Extended operator reference for [`generating-dataflow-pipeline`](#generating-dataflow-pipeline).

Per-operator API documentation for all text processing operators used by the pipeline generator. When the 6 core primitives in `generating-dataflow-pipeline/SKILL.md` don't cover your task, consult the detailed references here.

### Available Operators

**Generate** (`core_text/generate/`)

- `prompted-generator` - Basic LLM generation
- `format-str-prompted-generator` - Template-based generation
- `chunked-prompted-generator` - Chunked text generation
- `embedding-generator` - Generate embeddings
- `retrieval-generator` - RAG generation
- `bench-answer-generator` - Generate benchmark answers
- `text2multihopqa-generator` - Multi-hop QA generation
- `random-domain-knowledge-row-generator` - Random domain knowledge generation

**Filter** (`core_text/filter/`)

- `prompted-filter` - LLM scoring and filtering
- `general-filter` - Rule-based numeric filtering
- `kcentergreedy-filter` - Diversity-based filtering

**Refine** (`core_text/refine/`)

- `prompted-refiner` - LLM-based text rewriting
- `pandas-operator` - Custom pandas operations

**Eval** (`core_text/eval/`)

- `prompted-evaluator` - LLM scoring
- `bench-dataset-evaluator` - Evaluate benchmark datasets
- `bench-dataset-evaluator-question` - Evaluate benchmark questions
- `text2qa-sample-evaluator` - Evaluate QA samples
- `unified-bench-dataset-evaluator` - Unified evaluation

### Directory Structure

Each operator folder contains:

- `SKILL.md` - English skill documentation describing use cases, usage, imports, parameters, and examples
- `SKILL_zh.md` - Chinese documentation
- `examples/good.md` - Correct usage with simple single-operator pipeline, sample input and output
- `examples/bad.md` - Common mistakes

---

## `dataflow-operator-builder`

Production-grade scaffold skill for new DataFlow operators (`generate/filter/refine/eval`), including templates, CLI wrappers, and tests.

### What This Skill Is For

- Use it when you need a new operator package that is immediately runnable in a real repo, not just a single class file.
- It is especially useful when you want structure consistency across teams: same package layout, same CLI style, and same baseline tests.

### What You Get After One Run

- A complete operator implementation for one type: `generate`, `filter`, `refine`, or `eval`.
- A separate CLI module under `cli/`, so the operator can be run in batch jobs without writing extra glue code.
- Baseline test files (`unit`, `registry`, `smoke`) so the operator is easier to validate in CI from day one.

### How It Works in Practice

1. You describe the operator contract through a spec (package name, operator type, class/module names, input/output keys, and whether it uses LLM).
2. The skill validates the spec and applies template rules from `references/` to avoid common contract and registration mistakes.
3. It renders files into your target repo and can run in preview mode first (`--dry-run`) so you can inspect changes before writing.
4. You fill in business logic details where needed, then run the generated tests and CLI for a quick end-to-end check.

### Typical Usage

- Chat entry: `/dataflow-operator-builder`
- Direct spec entry: `/dataflow-operator-builder --spec path/to/spec.json --output-root path/to/repo`

### Minimal Spec Example

```json
{
  "package_name": "dataflow_ext_demo",
  "operator_type": "filter",
  "operator_class_name": "DemoQualityFilter",
  "operator_module_name": "demo_quality_filter",
  "input_key": "raw_text",
  "output_key": "is_valid",
  "uses_llm": false
}
```

### Input Expectations

- Required: `package_name`, `operator_type`, `operator_class_name`, `operator_module_name`, `input_key`, `output_key`, `uses_llm`.
- Optional but common in real projects: `cli_module_name`, `test_file_prefix`, `overwrite_strategy`, `validation_level`.

### A Concrete Scenario

- Suppose you need a `filter` operator that removes low-quality records before expensive generation.
- With this skill, you can quickly scaffold a consistent package, plug in your filtering rules, and immediately run registry/smoke tests.
- This reduces the usual setup time (folder layout, imports, registration, CLI wiring, test skeletons) and lets you focus on operator logic.

### Helpful Flags

- `--dry-run`: preview create/update plan without modifying files.
- `--overwrite {ask-each,overwrite-all,skip-existing}`: control overwrite behavior safely in existing repos.
- `--validation-level {none,basic,full}`: choose how strict pre-write checks should be.

### Minimal Run Command

```bash
python dataflow-operator-builder/scripts/build_operator_artifacts.py \
  --spec /tmp/operator_spec.json \
  --output-root . \
  --dry-run
```

---

## `prompt-template-builder`

Production-oriented skill for building/revising DataFlow prompt templates/configs for existing operators, with two-round AskUserQuestion intake, two-stage auditable outputs, and static acceptance walkthrough.

### What This Skill Is For

- Use it when an existing operator needs a new prompt template, or when an old template starts failing on quality, format stability, or business constraints.
- It is built for production updates where you need clear reasoning and traceability, not just a rewritten prompt string.

### What Makes It Different

- It first checks operator compatibility and picks the right template style (for example `DIYPromptABC` or `FormatStrPrompt`) so your final output matches operator expectations.
- It returns auditable two-stage outputs, which helps reviewers understand both the decision process and the final artifact.

### How the Two Stages Help Review

1. Stage 1 (decision JSON): explains why a specific template/config strategy was chosen, how arguments are mapped, what output contract is enforced, and which static checks must pass.
2. Stage 2 (final deliverable): provides the final template/config, integration snippet, and a checklist-style walkthrough that can be copied into code review or QA notes.

### Typical Usage

- Chat entry: `/prompt-template-builder`
- Direct spec entry: `/prompt-template-builder --spec path/to/prompt_spec.json`

### Minimal Spec Example

```json
{
  "Target": "Generate concise e-commerce selling points",
  "OP_NAME": "PromptedGenerator",
  "Constraints": "Professional tone; <= 80 Chinese chars",
  "Arguments": ["product_name", "category"]
}
```

### Input Expectations

- Required: `Target`, `OP_NAME`.
- Optional but strongly recommended: `Constraints`, `Expected Output`, `Arguments`, `Sample Cases`, `Tone/Style`, `Validation Focus`.

### A Concrete Scenario

- You have a `PromptedGenerator` that should generate short e-commerce selling points, but outputs are too long and style is inconsistent.
- You can provide the business target, length/style constraints, and sample inputs.
- The skill then produces a type-aligned prompt solution plus validation notes, so you can quickly test whether output length and tone are now stable.

### Expected Output Shape

- A Stage 1 decision record (strategy, mapping, checks such as `prompt_template_type_aligned`).
- A Stage 2 implementation package (template/config content, integration guidance, and acceptance walkthrough).
