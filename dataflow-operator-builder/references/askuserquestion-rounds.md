# AskUserQuestion Round Design

Use **exactly two rounds**, each in one batch.

## Round 1: Structure

Recommended question blocks:

1. Operator family
- `generate` (Recommended): content generation/transformation
- `filter`: keep/discard based on criteria
- `refine`: cleanup/normalization/improvement
- `eval`: scoring/evaluation output

2. Operator identity
- class name
- module file name

3. Repository placement
- package name
- output root

4. LLM dependency
- yes/no

5. CLI module name
- default `<operator_module>_cli.py`

## Round 2: Implementation

1. IO keys
- `input_key`
- `output_key`

2. Description style
- bilingual zh/en (Recommended)
- zh only
- en only

3. CLI arguments
- default-only (Recommended)
- include custom args

4. Test prefix
- default from module name (Recommended)
- custom prefix

5. Overwrite strategy
- ask-each (Recommended)
- overwrite-all
- skip-existing

## Important

- Present meaningful options only.
- Include a recommended option and short reason.
- Do not ask one question at a time.
