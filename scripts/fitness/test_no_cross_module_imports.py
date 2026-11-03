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
        allow.write_text("# header\n\n# legacy bridge, ticket 42\n"
                         "models/**: odoo.addons.sale.models.*\n")
        proc = self.run_cli(a, env_allow=allow)
        self.assertEqual(proc.returncode, 0, proc.stdout)

    def test_allow_flag_repeatable(self):
        a = self.addon("mine")
        self.write(a, "models/m.py", (
            "from odoo.addons.sale.models.x import Y\n"
            "from odoo.addons.stock.models.x import Z\n"
        ))
        proc = self.run_cli(a, "--allow", "models/**: odoo.addons.sale.*  # why",
                            "--allow", "models/**: odoo.addons.stock.*  # why")
        self.assertEqual(proc.returncode, 0, proc.stdout)
        proc = self.run_cli(a, "--allow", "models/**: odoo.addons.sale.*  # why")
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


class TestEvasionForms(FixtureCase):
    """Gaps 1-2: routes to another addon that are not import statements."""

    def flagged(self, source, tag="MODULE-ISOLATION "):
        a = self.addon("mine")
        self.write(a, "models/m.py", source)
        proc = self.run_cli(a)
        lines = [ln for ln in self.violation_lines(proc) if tag in ln]
        return proc, lines

    def assert_caught(self, source, line_no, tag="MODULE-ISOLATION "):
        proc, lines = self.flagged(source, tag)
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(len(lines), 1, proc.stdout)
        self.assertIn("m.py:%d:" % line_no, lines[0])
        return lines[0]

    def test_from_odoo_import_addons_attribute(self):
        line = self.assert_caught(
            "from odoo import addons\n"
            "X = addons.sale.models.sale_order.SaleOrder\n", 2)
        self.assertIn("mine imports sale via 'addons.sale.models.sale_order.SaleOrder'", line)

    def test_import_odoo_attribute(self):
        self.assert_caught("import odoo\nX = odoo.addons.sale.models.x\n", 2)

    def test_aliased_addons_package(self):
        self.assert_caught("import odoo.addons as oa\nX = oa.sale.models\n", 2)

    def test_importlib_literal(self):
        line = self.assert_caught(
            "import importlib\nm = importlib.import_module('odoo.addons.sale.models')\n", 2)
        self.assertIn("mine imports sale", line)

    def test_from_importlib_import_module_alias(self):
        self.assert_caught(
            "from importlib import import_module as im\nm = im('odoo.addons.sale')\n", 2)

    def test_dunder_import_literal(self):
        self.assert_caught("m = __import__('odoo.addons.sale')\n", 1)

    def test_folded_string_concatenation(self):
        self.assert_caught(
            "import importlib\nm = importlib.import_module('odoo.' + 'addons.sale')\n", 2)

    def test_computed_name_flagged_dynamic(self):
        line = self.assert_caught(
            "import importlib\nn = 'x'\nm = importlib.import_module(n)\n", 3,
            tag="MODULE-ISOLATION-DYNAMIC")
        self.assertIn("<dynamic>", line)

    def test_dynamic_can_be_allow_listed(self):
        a = self.addon("mine")
        self.write(a, "models/m.py", "import importlib\nm = importlib.import_module(n)\n")
        proc = self.run_cli(a, "--allow", "models/m.py: <dynamic>  # plugin loader")
        self.assertEqual(proc.returncode, 0, proc.stdout)
        self.assertIn("ALLOWED", proc.stdout)

    def test_no_false_positives_for_benign_forms(self):
        a = self.addon("mine")
        self.write(a, "models/m.py", (
            "import importlib\nimport odoo\nfrom odoo import addons\n"
            "from odoo.tools import float_compare\n"
            "a = importlib.import_module('json')\n"
            "b = importlib.import_module('.sibling', __package__)\n"
            "c = __import__('os')\n"
            "c2 = __import__('region_%s' % n, globals(), locals(), ['X'], 1)\n"
            "c3 = __import__(n, level=1)\n"
            "d = odoo.tools.float_compare\n"
            "e = addons.mine.models\n"
            "f = addons.__path__\n"
            "g = self_env = 'odoo.addons.sale'\n"
        ))
        proc = self.run_cli(a)
        self.assertEqual(proc.returncode, 0, proc.stdout)

    def test_prefilter_does_not_skip_split_strings(self):
        # no 'odoo.addons' substring anywhere in the file
        self.assert_caught(
            "from importlib import import_module\nimport_module('odoo.' 'addons.sale')\n", 2)


class TestAllowListReportingAndJustification(FixtureCase):
    """Gaps 3, 4 and 6."""

    def setup_violation(self):
        a = self.addon("mine")
        self.write(a, "models/m.py", "from odoo.addons.sale.models import x\n")
        return a

    def test_allowed_import_is_reported_with_rule_and_reason(self):
        a = self.setup_violation()
        proc = self.run_cli(a, "--allow", "models/m.py: odoo.addons.sale.*  # bridge, T-42")
        self.assertEqual(proc.returncode, 0, proc.stdout)
        allowed = [ln for ln in proc.stdout.splitlines() if " ALLOWED " in ln]
        self.assertEqual(len(allowed), 1, proc.stdout)
        self.assertIn("models/m.py:1:", allowed[0])
        self.assertIn("bridge, T-42", allowed[0])
        self.assertIn("0 violation(s) in 2 file(s) scanned; 1 allowed", proc.stdout)

    def test_file_rule_without_justification_is_usage_error(self):
        a = self.setup_violation()
        allow = self.root / "bad.allow"
        allow.write_text("# a reason that is separated by a blank line\n\n"
                         "models/**: odoo.addons.sale.*\n")
        proc = self.run_cli(a, env_allow=allow)
        self.assertEqual(proc.returncode, 2, proc.stdout)
        self.assertIn("justification", proc.stderr)
        self.assertIn("bad.allow:3", proc.stderr)

    def test_empty_comment_is_not_a_justification(self):
        a = self.setup_violation()
        allow = self.root / "bad.allow"
        allow.write_text("#\nmodels/**: odoo.addons.sale.*   #   \n")
        proc = self.run_cli(a, env_allow=allow)
        self.assertEqual(proc.returncode, 2, proc.stdout)

    def test_inline_justification_accepted(self):
        a = self.setup_violation()
        allow = self.root / "ok.allow"
        allow.write_text("models/**: odoo.addons.sale.*  # bridge\n")
        proc = self.run_cli(a, env_allow=allow)
        self.assertEqual(proc.returncode, 0, proc.stdout)

    def test_cli_rule_without_justification_is_usage_error(self):
        a = self.setup_violation()
        proc = self.run_cli(a, "--allow", "models/**: odoo.addons.sale.*")
        self.assertEqual(proc.returncode, 2)
        self.assertIn("justification", proc.stderr)

    def test_extra_allow_sources_add_to_default(self):
        # Gap 6: env / --allow-file must not drop the default tests/** rule
        a = self.addon("mine")
        self.write(a, "tests/test_a.py",
                   "from odoo.addons.sale.tests.common import TestSaleCommon\n")
        self.write(a, "models/m.py", "from odoo.addons.sale.models import x\n")
        extra = self.root / "extra.allow"
        extra.write_text("models/**: odoo.addons.sale.models  # bridge\n")
        for args, env in (((), extra), (("--allow-file", extra), None)):
            proc = self.run_cli(a, *args, env_allow=env)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertIn("; 2 allowed", proc.stdout)

    def test_no_default_allow_drops_default(self):
        a = self.addon("mine")
        self.write(a, "tests/test_a.py",
                   "from odoo.addons.sale.tests.common import TestSaleCommon\n")
        proc = self.run_cli(a, "--no-default-allow", env_allow=None)
        self.assertEqual(proc.returncode, 1, proc.stdout)

    def test_default_allow_file_is_valid(self):
        mod = load_module()
        rules = mod.load_rules_file(mod.DEFAULT_ALLOW_FILE)
        self.assertTrue(rules)
        self.assertTrue(all(r.justification for r in rules))


class TestJsonOutput(FixtureCase):
    """Gap 5."""

    def test_json_violations_and_allowed(self):
        import json
        a = self.addon("mine")
        self.write(a, "models/m.py", (
            "from odoo.addons.sale.models import x\n"
            "from odoo.addons.stock.models import y\n"
        ))
        proc = self.run_cli(a, "--format", "json",
                            "--allow", "models/**: odoo.addons.stock.*  # bridge")
        self.assertEqual(proc.returncode, 1, proc.stdout)
        data = json.loads(proc.stdout)
        self.assertEqual(data["exit_code"], 1)
        self.assertEqual(data["files_scanned"], 2)
        self.assertEqual([(v["target"], v["line"], v["kind"]) for v in data["violations"]],
                         [("sale", 1, "import")])
        self.assertEqual(data["allowed"][0]["target"], "stock")
        self.assertEqual(data["allowed"][0]["justification"], "bridge")
        self.assertTrue(data["violations"][0]["path"].endswith("mine/models/m.py"))

    def test_json_clean_and_usage_error(self):
        import json
        a = self.addon("mine")
        proc = self.run_cli(a, "--format", "json")
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(json.loads(proc.stdout)["violations"], [])
        proc = self.run_cli(self.root / "nope", "--format", "json")
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(json.loads(proc.stdout)["exit_code"], 2)


if __name__ == "__main__":
    unittest.main()
