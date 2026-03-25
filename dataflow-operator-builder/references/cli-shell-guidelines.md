# CLI Shell Guidelines

## Why Separate CLI from Operator

Operators should remain composable and pipeline-friendly.
CLI wrappers should handle:
- argument parsing
- runtime parameter collection
- optional LLM serving initialization
- invoking operator with `DataFlowStorage`

## CLI Structure

Recommended steps:
1. Parse CLI args
2. Build storage (`FileStorage`)
3. Optionally build LLM serving backend
4. Create operator instance
5. Call `operator.run(storage=storage.step(), ...)`
6. Print result key and output location

## Human-in-the-Loop

CLI can include confirmation prompts, but do not put heavy prompts inside operator core.
