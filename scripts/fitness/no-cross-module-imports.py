#!/usr/bin/env python3
"""Fitness function: module isolation (no cross-addon Python imports).

Principle
    An Odoo addon (any directory containing ``__manifest__.py``) must not
    import Python code from another addon. Addons talk to each other through
    the ORM registry, not through the import system.

    Forbidden:
        from odoo.addons.sale.models.sale_order import SaleOrder
        import odoo.addons.sale.models
        from odoo.addons import sale
        import odoo.addons.sale as s
    Correct:
        self.env['sale.order']
    Always allowed: relative imports, an addon importing its own package
    (``odoo.addons.<self>...``), and anything outside ``odoo.addons``.

Why
    Direct imports create hidden load-order and install-order coupling that
    the manifest ``depends`` list does not describe, and break when the other
    addon is not installed. ``self.env['model.name']`` keeps the dependency
    explicit and resolvable at runtime.

How the Code Reviewer uses it
    Run on every build against the changed addons (default: custom_addons/):
        python scripts/fitness/no-cross-module-imports.py
    Any output line is a blocking finding. Output is deterministic (sorted)
    and one finding per line: ``<path>:<line>: MODULE-ISOLATION ...``.

Allow-list
    Rules live in ``scripts/fitness/no-cross-module-imports.allow`` (or the
    file named by env var FITNESS_ALLOWLIST, or --allow-file) and in repeated
    --allow options. Rule format, one per line, ``#`` starts a comment:

        <path-glob>: <module-glob>

    <path-glob> is an fnmatch pattern matched against the file path relative
    to its addon root (posix separators; ``*`` also crosses ``/``).
    <module-glob> is an fnmatch pattern matched against the imported dotted
    module (a rule also covers its submodules). A rule without ``:`` is a
    module-glob that applies to every path. Default rule:

        tests/**: odoo.addons.*.tests.common

Output and exit codes
    Findings and the summary line ``N violation(s) in M file(s) scanned`` are
    written to stdout. Files that cannot be parsed are reported as findings
    (``MODULE-ISOLATION-ERROR``) and count as violations. For speed, files
    whose text never contains ``odoo.addons`` are not parsed at all, so only
    unparsable files that mention it are reported.
    0 = clean, 1 = violations found, 2 = usage error (bad path, bad rule,
    unreadable allow-list file).
"""
import argparse
import ast
import fnmatch
import os
import sys
from pathlib import Path
from typing import List, NamedTuple, Optional, Sequence, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_PATHS = ["custom_addons"]
DEFAULT_ALLOW_FILE = Path(__file__).resolve().with_name("no-cross-module-imports.allow")
ALLOW_ENV_VAR = "FITNESS_ALLOWLIST"
ADDONS_PREFIX = "odoo.addons."
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".claude-logs"}

Rule = Tuple[str, str]  # (path_glob, module_glob)


class Violation(NamedTuple):
    path: Path
    line: int
    addon: str
    target: str
    text: str
    error: Optional[str] = None


class UsageError(Exception):
    pass


def parse_rule(raw: str) -> Rule:
    """Parse ``<path-glob>: <module-glob>`` (or a bare module-glob)."""
    if ":" in raw:
        path_glob, _, module_glob = raw.partition(":")
    else:
        path_glob, module_glob = "*", raw
    path_glob, module_glob = path_glob.strip(), module_glob.strip()
    if not path_glob or not module_glob:
        raise UsageError("invalid allow rule: %r" % raw)
    return path_glob, module_glob


def load_rules_file(path: Path) -> List[Rule]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise UsageError("cannot read allow-list file %s: %s" % (path, exc))
    rules = []
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            rules.append(parse_rule(line))
    return rules


def is_allowed(rel_path: str, module: str, rules: Sequence[Rule]) -> bool:
    for path_glob, module_glob in rules:
        if not fnmatch.fnmatchcase(rel_path, path_glob):
            continue
        if fnmatch.fnmatchcase(module, module_glob) or fnmatch.fnmatchcase(
                module, module_glob + ".*"):
            return True
    return False


def addon_target(module: str) -> Optional[str]:
    """Return the addon name for ``odoo.addons.<addon>[.x]`` else None."""
    if not module.startswith(ADDONS_PREFIX):
        return None
    return module[len(ADDONS_PREFIX):].split(".", 1)[0] or None


def iter_statements(tree: ast.AST):
    """Yield every statement node, descending only through statement lists.

    Imports are statements, so skipping expression subtrees (unlike
    ``ast.walk``) finds the same imports several times faster.
    """
    stack = [tree]
    while stack:
        node = stack.pop()
        yield node
        for attr in ("body", "orelse", "finalbody", "handlers", "cases"):
            children = getattr(node, attr, None)
            if isinstance(children, list):
                stack.extend(children)


def imported_modules(tree: ast.AST):
    """Yield (lineno, dotted module, import text) for absolute imports."""
    for node in iter_statements(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                text = "import " + alias.name
                if alias.asname:
                    text += " as " + alias.asname
                yield node.lineno, alias.name, text
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            for alias in node.names:
                if alias.name == "*":
                    yield node.lineno, node.module, "from %s import *" % node.module
                    continue
                text = "from %s import %s" % (node.module, alias.name)
                if alias.asname:
                    text += " as " + alias.asname
                yield node.lineno, node.module + "." + alias.name, text


def scan_file(path: Path, addon_root: Path, addon_name: str,
              rules: Sequence[Rule]) -> List[Violation]:
    try:
        source = path.read_bytes()
        if b"odoo.addons" not in source:
            return []  # speed: such a file cannot contain a violating import
        tree = ast.parse(source, filename=str(path))
    except (SyntaxError, ValueError, OSError) as exc:
        line = getattr(exc, "lineno", None) or 1
        return [Violation(path, line, addon_name, "", "", "could not parse: %s" % exc)]
    rel = path.relative_to(addon_root).as_posix()
    found = []
    for lineno, module, text in imported_modules(tree):
        target = addon_target(module)
        if target is None or target == addon_name:
            continue
        if is_allowed(rel, module, rules):
            continue
        found.append(Violation(path, lineno, addon_name, target, text))
    return found


def find_addon_root(directory: Path, cache: dict) -> Optional[Path]:
    """Nearest ancestor (inclusive) containing __manifest__.py."""
    if directory in cache:
        return cache[directory]
    if (directory / "__manifest__.py").is_file():
        result = directory
    elif directory.parent == directory:
        result = None
    else:
        result = find_addon_root(directory.parent, cache)
    cache[directory] = result
    return result


def iter_python_files(target: Path):
    if target.is_file():
        yield target
        return
    for dirpath, dirnames, filenames in os.walk(target):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        for name in sorted(filenames):
            if name.endswith(".py"):
                yield Path(dirpath) / name


def display_path(path: Path) -> str:
    for base in (Path.cwd(), REPO_ROOT):
        try:
            return path.relative_to(base).as_posix()
        except ValueError:
            continue
    return path.as_posix()


def format_violation(v: Violation) -> str:
    where = "%s:%d:" % (display_path(v.path), v.line)
    if v.error:
        return "%s MODULE-ISOLATION-ERROR %s" % (where, v.error.replace("\n", " "))
    return ("%s MODULE-ISOLATION %s imports %s via '%s' - use self.env['<model>'] instead"
            % (where, v.addon, v.target, v.text))


def run(paths: Sequence[str], rules: Sequence[Rule]) -> Tuple[List[Violation], int]:
    targets = []
    for raw in paths:
        p = Path(raw)
        if not p.is_absolute():
            p = Path.cwd() / p
        if not p.exists():
            raise UsageError("path does not exist: %s" % raw)
        targets.append(p.resolve())
    cache: dict = {}
    seen = set()
    violations: List[Violation] = []
    scanned = 0
    for target in targets:
        for file in iter_python_files(target):
            if file in seen:
                continue
            seen.add(file)
            root = find_addon_root(file.parent, cache)
            if root is None:
                continue
            scanned += 1
            violations.extend(scan_file(file, root, root.name, rules))
    return violations, scanned


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fail when an Odoo addon imports another addon's Python "
                    "modules (use self.env['model.name'] instead). Exit codes: "
                    "0 clean, 1 violations, 2 usage error.",
        epilog="Allow rule format: '<path-glob>: <module-glob>' - path-glob is "
               "matched against the file path relative to its addon root, "
               "module-glob against the imported dotted module. Default rule: "
               "'tests/**: odoo.addons.*.tests.common'. Rules come from "
               "scripts/fitness/no-cross-module-imports.allow, or the file in "
               "env var FITNESS_ALLOWLIST, plus any --allow options.")
    parser.add_argument("paths", nargs="*",
                        help="files or directories to scan (default: custom_addons/ "
                             "at the repository root)")
    parser.add_argument("--allow", action="append", default=[], metavar="PATTERN",
                        help="extra allow rule '<path-glob>: <module-glob>' "
                             "(repeatable)")
    parser.add_argument("--allow-file", metavar="FILE",
                        help="allow-list file (overrides env FITNESS_ALLOWLIST "
                             "and the default file)")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        allow_file = args.allow_file or os.environ.get(ALLOW_ENV_VAR)
        if allow_file:
            rules = load_rules_file(Path(allow_file))
        elif DEFAULT_ALLOW_FILE.is_file():
            rules = load_rules_file(DEFAULT_ALLOW_FILE)
        else:
            rules = []
        rules += [parse_rule(r) for r in args.allow]
        paths = args.paths or [str(REPO_ROOT / p) for p in DEFAULT_PATHS]
        violations, scanned = run(paths, rules)
    except UsageError as exc:
        sys.stderr.write("error: %s\n" % exc)
        return 2
    lines = sorted(format_violation(v) for v in violations)
    for line in lines:
        sys.stdout.write(line + "\n")
    sys.stdout.write("%d violation(s) in %d file(s) scanned\n" % (len(lines), scanned))
    return 1 if lines else 0


if __name__ == "__main__":
    sys.exit(main())
