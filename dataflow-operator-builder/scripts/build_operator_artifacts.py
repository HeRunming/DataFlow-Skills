#!/usr/bin/env python3
"""Instantiate DataFlow operator scaffolds from templates."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

VALID_TYPES = {"generate", "filter", "refine", "eval"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build DataFlow operator artifacts from skill templates")
    parser.add_argument("--spec", required=True, help="Path to JSON spec")
    parser.add_argument("--output-root", required=True, help="Repository root to write generated files")
    parser.add_argument("--skill-dir", default=None, help="Skill directory; default is script parent")
    parser.add_argument("--overwrite", choices=["ask-each", "overwrite-all", "skip-existing"], default="ask-each")
    parser.add_argument("--dry-run", action="store_true", help="Print file plan without writing")
    return parser.parse_args()


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def validate_spec(spec: dict) -> dict:
    required = [
        "package_name",
        "operator_type",
        "operator_class_name",
        "operator_module_name",
        "input_key",
        "output_key",
        "uses_llm",
    ]
    missing = [k for k in required if k not in spec]
    if missing:
        raise ValueError(f"Missing required spec fields: {missing}")

    operator_type = str(spec["operator_type"]).strip().lower()
    if operator_type not in VALID_TYPES:
        raise ValueError(f"operator_type must be one of {sorted(VALID_TYPES)}, got: {operator_type}")

    module = str(spec["operator_module_name"]).strip().replace(".py", "")
    if not re.fullmatch(r"[a-zA-Z_][a-zA-Z0-9_]*", module):
        raise ValueError(f"Invalid operator_module_name: {module}")

    package = str(spec["package_name"]).strip()
    if not re.fullmatch(r"[a-zA-Z_][a-zA-Z0-9_]*", package):
        raise ValueError(f"Invalid package_name: {package}")

    class_name = str(spec["operator_class_name"]).strip()
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", class_name):
        raise ValueError(f"Invalid operator_class_name: {class_name}")

    test_prefix = spec.get("test_file_prefix") or module
    cli_module = spec.get("cli_module_name") or f"{module}_cli"
    cli_module = str(cli_module).replace(".py", "")

    spec = dict(spec)
    spec["operator_type"] = operator_type
    spec["operator_module_name"] = module
    spec["package_name"] = package
    spec["operator_class_name"] = class_name
    spec["test_file_prefix"] = test_prefix
    spec["cli_module_name"] = cli_module
    spec["uses_llm"] = bool(spec["uses_llm"])
    return spec


def render_conditionals(text: str, spec: dict) -> str:
    flags = {
        "USES_LLM": bool(spec["uses_llm"]),
        "NOT_USES_LLM": not bool(spec["uses_llm"]),
        "FILTER": spec["operator_type"] == "filter",
        "NOT_FILTER": spec["operator_type"] != "filter",
    }

    for name, enabled in flags.items():
        pattern = re.compile(rf"\[\[IF_{name}\]\](.*?)\[\[END_IF_{name}\]\]", re.DOTALL)
        text = pattern.sub(lambda m: m.group(1) if enabled else "", text)
    return text


def render_placeholders(text: str, mapping: dict) -> str:
    for key, value in mapping.items():
        text = text.replace(f"{{{{{key}}}}}", str(value))
    return text


def read_template(path: Path, spec: dict, mapping: dict) -> str:
    text = path.read_text(encoding="utf-8")
    text = render_conditionals(text, spec)
    text = render_placeholders(text, mapping)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = "\n".join(line.rstrip() for line in text.splitlines()) + "\n"
    return text


def build_file_plan(skill_dir: Path, output_root: Path, spec: dict) -> list[tuple[Path, Path]]:
    pkg = spec["package_name"]
    t = spec["operator_type"]
    module = spec["operator_module_name"]
    prefix = spec["test_file_prefix"]
    cli_module = spec["cli_module_name"]

    return [
        (
            skill_dir / "assets" / "templates" / "operators" / f"{t}_operator.py.tmpl",
            output_root / pkg / "operators" / t / f"{module}.py",
        ),
        (
            skill_dir / "assets" / "templates" / "cli" / "operator_cli.py.tmpl",
            output_root / pkg / "cli" / f"{cli_module}.py",
        ),
        (
            skill_dir / "assets" / "templates" / "tests" / "test_operator_unit.py.tmpl",
            output_root / "test" / f"test_{prefix}_unit.py",
        ),
        (
            skill_dir / "assets" / "templates" / "tests" / "test_operator_registry.py.tmpl",
            output_root / "test" / f"test_{prefix}_registry.py",
        ),
        (
            skill_dir / "assets" / "templates" / "tests" / "test_operator_smoke.py.tmpl",
            output_root / "test" / f"test_{prefix}_smoke.py",
        ),
        (
            skill_dir / "assets" / "templates" / "package" / "package_init.py.tmpl",
            output_root / pkg / "__init__.py",
        ),
        (
            skill_dir / "assets" / "templates" / "package" / "operators_root_init.py.tmpl",
            output_root / pkg / "operators" / "__init__.py",
        ),
        (
            skill_dir / "assets" / "templates" / "package" / "operator_pkg_init.py.tmpl",
            output_root / pkg / "operators" / t / "__init__.py",
        ),
        (
            skill_dir / "assets" / "templates" / "package" / "cli_init.py.tmpl",
            output_root / pkg / "cli" / "__init__.py",
        ),
    ]


def print_plan(plan: list[tuple[Path, Path]]) -> None:
    print("\nPlanned outputs:")
    for _, dest in plan:
        tag = "UPDATE" if dest.exists() else "CREATE"
        print(f"  - [{tag}] {dest}")


def choose_action(dest: Path, overwrite_mode: str) -> str:
    if not dest.exists():
        return "write"
    if overwrite_mode == "overwrite-all":
        return "write"
    if overwrite_mode == "skip-existing":
        return "skip"

    while True:
        answer = input(f"File exists: {dest}\nChoose [o]verwrite / [s]kip / [q]uit: ").strip().lower()
        if answer in {"o", "overwrite"}:
            return "write"
        if answer in {"s", "skip"}:
            return "skip"
        if answer in {"q", "quit"}:
            return "quit"


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def write_files(plan: list[tuple[Path, Path]], spec: dict, overwrite_mode: str) -> dict:
    mapping = {
        "PACKAGE_NAME": spec["package_name"],
        "OPERATOR_TYPE": spec["operator_type"],
        "OPERATOR_CLASS_NAME": spec["operator_class_name"],
        "OPERATOR_MODULE": spec["operator_module_name"],
        "INPUT_KEY": spec["input_key"],
        "OUTPUT_KEY": spec["output_key"],
    }

    summary = {"written": [], "skipped": []}
    for template_path, dest in plan:
        action = choose_action(dest, overwrite_mode)
        if action == "quit":
            raise KeyboardInterrupt("User cancelled during overwrite selection")
        if action == "skip":
            summary["skipped"].append(dest)
            continue

        rendered = read_template(template_path, spec=spec, mapping=mapping)
        ensure_parent(dest)
        dest.write_text(rendered, encoding="utf-8")
        summary["written"].append(dest)

    return summary


def main() -> int:
    args = parse_args()
    script_dir = Path(__file__).resolve().parent
    skill_dir = Path(args.skill_dir).resolve() if args.skill_dir else script_dir.parent
    output_root = Path(args.output_root).resolve()

    spec = validate_spec(load_json(Path(args.spec).resolve()))
    plan = build_file_plan(skill_dir=skill_dir, output_root=output_root, spec=spec)

    print("DataFlow Operator Builder")
    print(f"Skill dir   : {skill_dir}")
    print(f"Output root : {output_root}")
    print(f"Overwrite   : {args.overwrite}")
    print(f"Dry run     : {args.dry_run}")

    print_plan(plan)

    if args.dry_run:
        print("\nDry-run complete. No files were written.")
        return 0

    confirm = input("\nProceed with file generation? [y/N]: ").strip().lower()
    if confirm not in {"y", "yes"}:
        print("Cancelled.")
        return 1

    summary = write_files(plan=plan, spec=spec, overwrite_mode=args.overwrite)
    print("\nGeneration complete.")
    print(f"Written ({len(summary['written'])}):")
    for path in summary["written"]:
        print(f"  - {path}")
    print(f"Skipped ({len(summary['skipped'])}):")
    for path in summary["skipped"]:
        print(f"  - {path}")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nCancelled by user.")
        raise SystemExit(130)
