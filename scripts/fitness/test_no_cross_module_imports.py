"""Tests for scripts/fitness/no-cross-module-imports.py (stdlib unittest).

Run: python -m unittest scripts/fitness/test_no_cross_module_imports.py -v
"""
import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "no-cross-module-imports.py"


def load_module():
    spec = importlib.util.spec_from_file_location("fitness_nxmi", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FixtureCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        # An empty allow-list file keeps the real default out of the way
        self.empty_allow = self.root / "empty.allow"
        self.empty_allow.write_text("# none\n", encoding="utf-8")

    def addon(self, name):
        path = self.root / name
        path.mkdir(parents=True, exist_ok=True)
        (path / "__manifest__.py").write_text("{'name': '%s'}\n" % name)
        return path

    def write(self, addon, rel, content):
        path = addon / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def run_cli(self, *args, env_allow="__default__"):
        env = dict(os.environ)
        env.pop("FITNESS_ALLOWLIST", None)
        if env_allow is None:
            pass
        elif env_allow == "__default__":
            env["FITNESS_ALLOWLIST"] = str(self.empty_allow)
        else:
            env["FITNESS_ALLOWLIST"] = str(env_allow)
        return subprocess.run(
            [sys.executable, str(SCRIPT), *map(str, args)],
            capture_output=True, text=True, env=env, cwd=str(self.root),
        )

    def violation_lines(self, proc):
        return [ln for ln in proc.stdout.splitlines() if "MODULE-ISOLATION" in ln]


class TestForbiddenForms(FixtureCase):
    def check(self, source, expect_text):
        a = self.addon("mine")
        self.write(a, "models/m.py", source)
        proc = self.run_cli(a)
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        lines = self.violation_lines(proc)
        self.assertEqual(len(lines), 1, proc.stdout)
        self.assertIn("mine imports sale via '%s'" % expect_text, lines[0])
        self.assertIn("self.env['<model>']", lines[0])
        self.assertTrue(lines[0].startswith("mine/models/m.py:1:") or ":1:" in lines[0])

    def test_from_import_submodule(self):
        self.check("from odoo.addons.sale.models.sale_order import SaleOrder\n",
                   "from odoo.addons.sale.models.sale_order import SaleOrder")

    def test_plain_import(self):
        self.check("import odoo.addons.sale.models\n", "import odoo.addons.sale.models")

    def test_from_addons_import_addon(self):
        self.check("from odoo.addons import sale\n", "from odoo.addons import sale")

    def test_import_alias(self):
        self.check("import odoo.addons.sale as s\n", "import odoo.addons.sale as s")

    def test_nested_in_function_and_try(self):
        a = self.addon("mine")
        self.write(a, "models/m.py", (
            "def f():\n"
            "    try:\n"
            "        from odoo.addons.sale.models import x\n"
            "    except ImportError:\n"
            "        pass\n"
        ))
        proc = self.run_cli(a)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("m.py:3:", self.violation_lines(proc)[0])


class TestAllowedForms(FixtureCase):
    def test_self_import_and_relative_and_core(self):
        a = self.addon("mine")
        self.write(a, "models/m.py", (
            "from odoo.addons.mine.models.other import X\n"
            "from . import other\n"
            "from ..models import other as o2\n"
            "from odoo import models, fields\n"
            "import odoo.addons\n"
            "import os\n"
        ))
        proc = self.run_cli(a)
        self.assertEqual(proc.returncode, 0, proc.stdout)
        # m.py plus the fixture's __manifest__.py
        self.assertIn("0 violation(s) in 2 file(s) scanned", proc.stdout)

    def test_files_outside_any_addon_ignored(self):
        stray = self.root / "loose"
        stray.mkdir()
        (stray / "x.py").write_text("from odoo.addons.sale.models import y\n")
        proc = self.run_cli(stray)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(self.violation_lines(proc), [])


class TestTestsFixtureException(FixtureCase):
    def test_tests_common_allowed_only_in_tests_dir(self):
        a = self.addon("mine")
        src = "from odoo.addons.sale.tests.common import TestSaleCommon\n"
        self.write(a, "tests/test_a.py", src)
        self.write(a, "models/m.py", src)
        proc = self.run_cli(a, env_allow=None)  # real default allow-list
        self.assertEqual(proc.returncode, 1, proc.stdout)
        lines = self.violation_lines(proc)
        self.assertEqual(len(lines), 1, proc.stdout)
        self.assertIn("models/m.py", lines[0])

    def test_tests_non_common_flagged(self):
        a = self.addon("mine")
        self.write(a, "tests/test_a.py", "from odoo.addons.sale.tests.utils import U\n")
        proc = self.run_cli(a, env_allow=None)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("tests/test_a.py:1:", self.violation_lines(proc)[0])

    def test_tests_common_via_from_package_import(self):
        a = self.addon("mine")
        self.write(a, "tests/test_a.py", "from odoo.addons.sale.tests import common\n")
        proc = self.run_cli(a, env_allow=None)
        self.assertEqual(proc.returncode, 0, proc.stdout)


class TestAllowListConfig(FixtureCase):
    def test_custom_allow_file_via_env(self):
        a = self.addon("mine")
        self.write(a, "models/m.py", "from odoo.addons.sale.models.x import Y\n")
        allow = self.root / "custom.allow"
        allow.write_text("# comment\n\nmodels/**: odoo.addons.sale.models.*\n")
        proc = self.run_cli(a, env_allow=allow)
        self.assertEqual(proc.returncode, 0, proc.stdout)

    def test_allow_flag_repeatable(self):
        a = self.addon("mine")
        self.write(a, "models/m.py", (
            "from odoo.addons.sale.models.x import Y\n"
            "from odoo.addons.stock.models.x import Z\n"
        ))
        proc = self.run_cli(a, "--allow", "models/**: odoo.addons.sale.*",
                            "--allow", "models/**: odoo.addons.stock.*")
        self.assertEqual(proc.returncode, 0, proc.stdout)
        proc = self.run_cli(a, "--allow", "models/**: odoo.addons.sale.*")
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(len(self.violation_lines(proc)), 1)

    def test_missing_env_allow_file_is_usage_error(self):
        a = self.addon("mine")
        proc = self.run_cli(a, env_allow=self.root / "nope.allow")
        self.assertEqual(proc.returncode, 2)


class TestRobustnessAndOutput(FixtureCase):
    def test_syntax_error_reported_not_crash(self):
        a = self.addon("mine")
        self.write(a, "models/bad.py", "import odoo.addons.sale\ndef (:\n")
        proc = self.run_cli(a)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("models/bad.py", proc.stdout)
        self.assertIn("could not parse", proc.stdout)
        self.assertNotIn("Traceback", proc.stderr)

    def test_output_sorted_and_deterministic(self):
        a = self.addon("mine")
        b = self.addon("another")
        self.write(a, "z.py", "import odoo.addons.sale\nimport odoo.addons.stock\n")
        self.write(a, "a.py", "import odoo.addons.sale\n")
        self.write(b, "m.py", "import odoo.addons.sale\n")
        first = self.run_cli(self.root)
        second = self.run_cli(self.root)
        self.assertEqual(first.stdout, second.stdout)
        lines = self.violation_lines(first)
        self.assertEqual(len(lines), 4)
        self.assertEqual(lines, sorted(lines))
        # 3 source files + 2 manifests scanned
        self.assertIn("4 violation(s) in 5 file(s) scanned", first.stdout)

    def test_nonexistent_path_exit_2(self):
        proc = self.run_cli(self.root / "does-not-exist")
        self.assertEqual(proc.returncode, 2)
        self.assertNotIn("Traceback", proc.stderr)

    def test_help_documents_allow_rule_format(self):
        proc = self.run_cli("--help")
        self.assertEqual(proc.returncode, 0)
        self.assertIn("--allow", proc.stdout)
        self.assertIn("FITNESS_ALLOWLIST", proc.stdout)


class TestUnitFunctions(FixtureCase):
    def test_find_violations_unit(self):
        mod = load_module()
        a = self.addon("mine")
        f = self.write(a, "m.py", "from odoo.addons import sale, stock\n")
        found = mod.scan_file(f, a, "mine", [])
        self.assertEqual([v.target for v in found], ["sale", "stock"])
        self.assertTrue(all(v.line == 1 for v in found))


if __name__ == "__main__":
    unittest.main()
