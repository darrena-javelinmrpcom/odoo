#!/usr/bin/env python3
"""Fitness function: module isolation (no cross-addon Python imports).

Principle
    An Odoo addon (any directory containing ``__manifest__.py``) must not
    import Python code from another addon. Addons talk to each other through
    the ORM registry, not through the import system.

    Forbidden (all detected):
        from odoo.addons.sale.models.sale_order import SaleOrder
        import odoo.addons.sale.models            (any nesting: def, try,
        from odoo.addons import sale               class body, if, with,
        import odoo.addons.sale as s               match/case)
        from odoo import addons; addons.sale.models.x      (attribute access
        import odoo; odoo.addons.sale.models.x              via an alias)
        importlib.import_module('odoo.addons.sale.models')  (literal or
        __import__('odoo.' + 'addons.sale')                  folded strings)
    Flagged for review (cannot be resolved statically):
        importlib.import_module(name) / __import__(name) with a computed name
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
    Run on every build against custom_addons/ (the default):
        python scripts/fitness/no-cross-module-imports.py [--format json]
    Every ``MODULE-ISOLATION`` / ``MODULE-ISOLATION-DYNAMIC`` /
    ``MODULE-ISOLATION-ERROR`` line is a blocking finding. ``ALLOWED`` lines
    are allow-listed imports, reported (never silently passed) with the rule
    and its justification; they do not fail the run. Output is deterministic
    (sorted), one finding per line: ``<path>:<line>: <TAG> ...``.

Allow-list
    Rules are read from ``scripts/fitness/no-cross-module-imports.allow``
    (always, unless --no-default-allow), PLUS the file named by env var
    FITNESS_ALLOWLIST, PLUS --allow-file, PLUS repeated --allow options.
    Extra sources add to the default; they never replace it.

    Rule format, one per line:

        # <justification>                       (comment line directly above)
        <path-glob>: <module-glob>
    or
        <path-glob>: <module-glob>  # <justification>   (inline)

    Every rule MUST carry a justification (a non-empty comment inline or on
    the line(s) directly above, with no blank line between). A rule without
    one is a usage error (exit 2). ``--allow`` takes the inline form.

    <path-glob> is an fnmatch pattern matched against the file path relative
    to its addon root (posix separators; ``*`` also crosses ``/``).
    <module-glob> is an fnmatch pattern matched against the imported dotted
    module (a rule also covers its submodules); unresolvable dynamic imports
    match the module name ``<dynamic>``. A rule without ``:`` is a module-glob
    that applies to every path. Default rule:

        tests/**: odoo.addons.*.tests.common

Output and exit codes
    Findings and the summary line ``N violation(s) in M file(s) scanned;
    K allowed`` go to stdout (or one JSON document with --format json).
    Files that cannot be parsed are reported as ``MODULE-ISOLATION-ERROR``
    and count as violations. For speed, files whose text contains none of
    ``addons``, ``import_module`` or ``__import__`` are not parsed, since
    they cannot contain a violation.
    0 = clean, 1 = violations found, 2 = usage error (bad path, bad or
    unjustified rule, unreadable allow-list file).
"""
import argparse
import ast
import fnmatch
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, NamedTuple, Optional, Sequence, Set, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_PATHS = ["custom_addons"]
DEFAULT_ALLOW_FILE = Path(__file__).resolve().with_name("no-cross-module-imports.allow")
ALLOW_ENV_VAR = "FITNESS_ALLOWLIST"
ADDONS_PKG = "odoo.addons"
ADDONS_PREFIX = ADDONS_PKG + "."
DYNAMIC = "<dynamic>"
PREFILTER_TOKENS = (b"addons", b"import_module", b"__import__")
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".claude-logs"}

KIND_IMPORT = "import"        # import statement
KIND_ATTRIBUTE = "attribute"  # odoo.addons.<x> reached through an alias
KIND_CALL = "call"            # importlib.import_module / __import__ literal
KIND_DYNAMIC = "dynamic"      # import_module / __import__ with computed name
KIND_ERROR = "parse-error"


class Rule(NamedTuple):
    path_glob: str
    module_glob: str
    justification: str
    source: str  # "<file>:<line>" or "--allow"

    def pattern(self) -> str:
        return "%s: %s" % (self.path_glob, self.module_glob)


class Finding(NamedTuple):
    path: Path
    line: int
    addon: str
    target: str
    module: str
    text: str
    kind: str
    rule: Optional[Rule] = None  # set => allow-listed, not a violation
    error: Optional[str] = None


class UsageError(Exception):
    pass


# --------------------------------------------------------------------------
# Allow-list
# --------------------------------------------------------------------------

def parse_rule(raw: str, justification: str, source: str) -> Rule:
    """Parse ``<path-glob>: <module-glob>`` (or a bare module-glob)."""
    if ":" in raw:
        path_glob, _, module_glob = raw.partition(":")
    else:
        path_glob, module_glob = "*", raw
    path_glob, module_glob = path_glob.strip(), module_glob.strip()
    if not path_glob or not module_glob:
        raise UsageError("%s: invalid allow rule: %r" % (source, raw))
    justification = justification.strip()
    if not justification:
        raise UsageError(
            "%s: allow rule %r has no justification comment (add '# <why>' "
            "inline or on the line directly above)" % (source, raw.strip()))
    return Rule(path_glob, module_glob, justification, source)


def parse_cli_rule(raw: str) -> Rule:
    rule, _, justification = raw.partition("#")
    return parse_rule(rule, justification, "--allow")


def load_rules_file(path: Path) -> List[Rule]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise UsageError("cannot read allow-list file %s: %s" % (path, exc))
    rules = []
    pending = ""  # nearest non-empty comment in the block directly above
    for lineno, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        if not stripped:
            pending = ""
            continue
        if stripped.startswith("#"):
            comment = stripped.lstrip("#").strip()
            if comment:
                pending = comment
            continue
        body, _, inline = stripped.partition("#")
        rules.append(parse_rule(body, inline.strip() or pending,
                                "%s:%d" % (display_path(path), lineno)))
        pending = ""
    return rules


def match_rule(rel_path: str, module: str, rules: Sequence[Rule]) -> Optional[Rule]:
    for rule in rules:
        if not fnmatch.fnmatchcase(rel_path, rule.path_glob):
            continue
        if fnmatch.fnmatchcase(module, rule.module_glob) or fnmatch.fnmatchcase(
                module, rule.module_glob + ".*"):
            return rule
    return None


# --------------------------------------------------------------------------
# Analysis
# --------------------------------------------------------------------------

def addon_target(module: str) -> Optional[str]:
    """Return the addon name for ``odoo.addons.<addon>[.x]`` else None."""
    if not module.startswith(ADDONS_PREFIX):
        return None
    name = module[len(ADDONS_PREFIX):].split(".", 1)[0]
    if not name or name.startswith("__"):  # odoo.addons.__path__ etc.
        return None
    return name


def fold_str(node: ast.AST) -> Optional[str]:
    """Constant-fold a str literal or a '+' concatenation of str literals."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left, right = fold_str(node.left), fold_str(node.right)
        if left is not None and right is not None:
            return left + right
    return None


def attribute_chain(node: ast.AST) -> Optional[List[str]]:
    """``a.b.c`` -> ['a', 'b', 'c'] when the chain is rooted at a Name."""
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if not isinstance(node, ast.Name):
        return None
    parts.append(node.id)
    return parts[::-1]


def unparse(node: ast.AST) -> str:
    try:
        return ast.unparse(node)
    except Exception:  # pragma: no cover - defensive, unparse is total in 3.9+
        return "<expr>"


class _Bindings(NamedTuple):
    pkg_aliases: Dict[str, str]  # local name -> 'odoo' | 'odoo.addons'
    importlib_names: Set[str]    # local names bound to the importlib module
    import_funcs: Set[str]       # local names bound to import_module/__import__


def collect_bindings(nodes: Sequence[ast.AST]) -> _Bindings:
    """File-wide (scope-insensitive) view of the aliases that matter."""
    pkg: Dict[str, str] = {}
    libs: Set[str] = set()
    funcs: Set[str] = {"__import__"}
    for node in nodes:
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.asname:
                    if alias.name in ("odoo", ADDONS_PKG):
                        pkg[alias.asname] = alias.name
                    elif alias.name == "importlib":
                        libs.add(alias.asname)
                elif alias.name == "odoo" or alias.name.startswith("odoo."):
                    pkg["odoo"] = "odoo"  # 'import odoo.x' binds 'odoo'
                elif alias.name == "importlib" or alias.name.startswith("importlib."):
                    libs.add("importlib")
        elif isinstance(node, ast.ImportFrom) and node.level == 0:
            for alias in node.names:
                local = alias.asname or alias.name
                if node.module == "odoo" and alias.name == "addons":
                    pkg[local] = ADDONS_PKG
                elif node.module == "importlib" and alias.name == "import_module":
                    funcs.add(local)
                elif node.module == "builtins" and alias.name == "__import__":
                    funcs.add(local)
    return _Bindings(pkg, libs, funcs)


def is_import_call(func: ast.AST, b: _Bindings) -> bool:
    if isinstance(func, ast.Name):
        return func.id in b.import_funcs
    if isinstance(func, ast.Attribute) and func.attr in ("import_module", "__import__"):
        root = func.value
        if func.attr == "import_module":
            return isinstance(root, ast.Name) and root.id in b.importlib_names
        return isinstance(root, ast.Name) and root.id == "builtins"
    return False


def is_relative_dunder_import(call: ast.Call) -> bool:
    """``__import__(name, g, l, fromlist, level)`` with a literal level >= 1
    (or a non-literal level) resolves inside the caller's own package."""
    level = call.args[4] if len(call.args) >= 5 else next(
        (k.value for k in call.keywords if k.arg == "level"), None)
    if level is None:
        return False
    return not (isinstance(level, ast.Constant) and level.value == 0)


def iter_hits(tree: ast.AST):
    """Yield (lineno, dotted module, source text, kind) for every route by
    which this file can reach another module under odoo.addons."""
    nodes = list(ast.walk(tree))
    b = collect_bindings(nodes)
    inner_attrs = {id(n.value) for n in nodes
                   if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Attribute)}
    for node in nodes:
        if isinstance(node, ast.Import):
            for alias in node.names:
                text = "import " + alias.name
                if alias.asname:
                    text += " as " + alias.asname
                yield node.lineno, alias.name, text, KIND_IMPORT
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            for alias in node.names:
                if alias.name == "*":
                    yield node.lineno, node.module, "from %s import *" % node.module, KIND_IMPORT
                    continue
                text = "from %s import %s" % (node.module, alias.name)
                if alias.asname:
                    text += " as " + alias.asname
                yield node.lineno, node.module + "." + alias.name, text, KIND_IMPORT
        elif isinstance(node, ast.Attribute) and id(node) not in inner_attrs:
            chain = attribute_chain(node)
            if chain and chain[0] in b.pkg_aliases:
                dotted = ".".join([b.pkg_aliases[chain[0]]] + chain[1:])
                if dotted.startswith(ADDONS_PREFIX):
                    yield node.lineno, dotted, unparse(node), KIND_ATTRIBUTE
        elif isinstance(node, ast.Call) and is_import_call(node.func, b):
            arg = node.args[0] if node.args else next(
                (k.value for k in node.keywords if k.arg == "name"), None)
            if arg is None or is_relative_dunder_import(node):
                continue
            name = fold_str(arg)
            if name is None:
                yield node.lineno, DYNAMIC, unparse(node), KIND_DYNAMIC
            elif not name.startswith("."):  # relative: stays inside the package
                yield node.lineno, name, unparse(node), KIND_CALL


def scan_file(path: Path, addon_root: Path, addon_name: str,
              rules: Sequence[Rule]) -> List[Finding]:
    """All cross-addon findings in one file; allow-listed ones carry ``rule``."""
    try:
        source = path.read_bytes()
        if not any(tok in source for tok in PREFILTER_TOKENS):
            return []  # speed: such a file cannot contain a violation
        tree = ast.parse(source, filename=str(path))
    except (SyntaxError, ValueError, OSError) as exc:
        line = getattr(exc, "lineno", None) or 1
        return [Finding(path, line, addon_name, "", "", "", KIND_ERROR,
                        error="could not parse: %s" % exc)]
    rel = path.relative_to(addon_root).as_posix()
    found = []
    for lineno, module, text, kind in iter_hits(tree):
        if kind == KIND_DYNAMIC:
            target = "?"
        else:
            target = addon_target(module)
            if target is None or target == addon_name:
                continue
        found.append(Finding(path, lineno, addon_name, target, module, text, kind,
                             rule=match_rule(rel, module, rules)))
    return found


# --------------------------------------------------------------------------
# Discovery
# --------------------------------------------------------------------------

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


def run(paths: Sequence[str], rules: Sequence[Rule]) -> Tuple[List[Finding], int]:
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
    findings: List[Finding] = []
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
            findings.extend(scan_file(file, root, root.name, rules))
    return findings, scanned


# --------------------------------------------------------------------------
# Output
# --------------------------------------------------------------------------

def display_path(path: Path) -> str:
    path = Path(path)
    for base in (Path.cwd(), REPO_ROOT):
        try:
            return path.resolve().relative_to(base.resolve()).as_posix()
        except (ValueError, OSError):
            continue
    return path.as_posix()


def format_finding(f: Finding) -> str:
    where = "%s:%d:" % (display_path(f.path), f.line)
    if f.kind == KIND_ERROR:
        return "%s MODULE-ISOLATION-ERROR %s" % (where, f.error.replace("\n", " "))
    if f.rule is not None:
        return ("%s ALLOWED %s imports %s via '%s' (rule '%s' at %s: %s)"
                % (where, f.addon, f.target, f.text, f.rule.pattern(),
                   f.rule.source, f.rule.justification))
    if f.kind == KIND_DYNAMIC:
        return ("%s MODULE-ISOLATION-DYNAMIC %s imports a runtime-computed module via "
                "'%s' - cannot verify isolation; use self.env['<model>'] or allow-list "
                "'%s' with a justification" % (where, f.addon, f.text, DYNAMIC))
    return ("%s MODULE-ISOLATION %s imports %s via '%s' - use self.env['<model>'] instead"
            % (where, f.addon, f.target, f.text))


def finding_json(f: Finding) -> dict:
    data = {"path": display_path(f.path), "line": f.line, "addon": f.addon,
            "kind": f.kind}
    if f.kind == KIND_ERROR:
        data["message"] = f.error
        return data
    data.update(target=f.target, module=f.module, text=f.text)
    if f.rule is not None:
        data.update(rule=f.rule.pattern(), rule_source=f.rule.source,
                    justification=f.rule.justification)
    return data


def sort_key(f: Finding):
    return (display_path(f.path), f.line, f.kind, f.text, f.error or "")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fail when an Odoo addon imports another addon's Python "
                    "modules (use self.env['model.name'] instead). Exit codes: "
                    "0 clean, 1 violations, 2 usage error.",
        epilog="Allow rule format: '<path-glob>: <module-glob>  # <justification>' "
               "(or the justification as a comment on the line directly above). "
               "path-glob is matched against the file path relative to its addon "
               "root, module-glob against the imported dotted module ('<dynamic>' "
               "for runtime-computed imports). A rule without a justification is "
               "a usage error. Default rule: 'tests/**: odoo.addons.*.tests.common'. "
               "Rules always come from scripts/fitness/no-cross-module-imports.allow "
               "(unless --no-default-allow), plus the file in env var "
               "FITNESS_ALLOWLIST, plus --allow-file, plus any --allow options. "
               "Allow-listed imports are still reported as ALLOWED lines.")
    parser.add_argument("paths", nargs="*",
                        help="files or directories to scan (default: custom_addons/ "
                             "at the repository root)")
    parser.add_argument("--allow", action="append", default=[], metavar="RULE",
                        help="extra allow rule '<path-glob>: <module-glob>  # <why>' "
                             "(repeatable; justification required)")
    parser.add_argument("--allow-file", metavar="FILE",
                        help="extra allow-list file (added to the default file "
                             "and FITNESS_ALLOWLIST, never replacing them)")
    parser.add_argument("--no-default-allow", action="store_true",
                        help="do not load the default allow-list file")
    parser.add_argument("--format", choices=("text", "json"), default="text",
                        help="output format (default: text)")
    return parser


def load_rules(args) -> List[Rule]:
    rules: List[Rule] = []
    if not args.no_default_allow and DEFAULT_ALLOW_FILE.is_file():
        rules += load_rules_file(DEFAULT_ALLOW_FILE)
    env_file = os.environ.get(ALLOW_ENV_VAR)
    if env_file:
        rules += load_rules_file(Path(env_file))
    if args.allow_file:
        rules += load_rules_file(Path(args.allow_file))
    rules += [parse_cli_rule(r) for r in args.allow]
    return rules


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        rules = load_rules(args)
        paths = args.paths or [str(REPO_ROOT / p) for p in DEFAULT_PATHS]
        findings, scanned = run(paths, rules)
    except UsageError as exc:
        if args.format == "json":
            sys.stdout.write(json.dumps({"exit_code": 2, "error": str(exc)}) + "\n")
        sys.stderr.write("error: %s\n" % exc)
        return 2
    findings.sort(key=sort_key)
    violations = [f for f in findings if f.rule is None]
    allowed = [f for f in findings if f.rule is not None]
    code = 1 if violations else 0
    if args.format == "json":
        sys.stdout.write(json.dumps({
            "exit_code": code,
            "files_scanned": scanned,
            "violations": [finding_json(f) for f in violations],
            "allowed": [finding_json(f) for f in allowed],
        }, indent=2) + "\n")
        return code
    for f in violations + allowed:
        sys.stdout.write(format_finding(f) + "\n")
    sys.stdout.write("%d violation(s) in %d file(s) scanned; %d allowed\n"
                     % (len(violations), scanned, len(allowed)))
    return code


if __name__ == "__main__":
    sys.exit(main())
