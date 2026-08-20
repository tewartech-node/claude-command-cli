"""Each rule gets two tests: it fires on the failure that taught it, and it
stays silent on correct code. The second is the more important one -- a rule
that cries wolf gets switched off, and a switched-off rule protects nothing."""

from __future__ import annotations

import pytest

from warnetech_curriculum.inspector import Inspector
from warnetech_curriculum.rules import RULES, RULES_BY_ID, run_rules


@pytest.fixture
def repo(tmp_path):
    """Builds a throwaway repo. Returns a writer plus a rule runner."""
    pkg = tmp_path / "app"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "engine.py").write_text(
        "class Engine:\n"
        "    def __init__(self):\n"
        "        self.items = []\n"
        "    def run(self):\n"
        "        return 1\n"
        "\n"
        "def helper(x):\n"
        "    return x\n",
        encoding="utf-8",
    )

    def write(name: str, source: str):
        target = pkg / name
        target.write_text(source, encoding="utf-8")
        return target

    def run(*names, only=None):
        inspector = Inspector(tmp_path)
        files = [pkg / n for n in names] if names else None
        return run_rules(inspector, files, only=only)

    return write, run


def ids(findings):
    return sorted({f.rule for f in findings})


# -- R001 ---------------------------------------------------------------------


def test_r001_flags_a_symbol_the_module_does_not_export(repo):
    write, run = repo
    write("bad.py", "from app.engine import Engine, reconstruct\n")
    findings = run("bad.py", only=["R001"])
    assert len(findings) == 1
    assert "does not export" in findings[0].message
    assert findings[0].severity == "critical"


def test_r001_flags_a_module_that_does_not_exist(repo):
    write, run = repo
    write("bad.py", "from app.database import get_client\n")
    findings = run("bad.py", only=["R001"])
    assert "does not exist" in findings[0].message


def test_r001_suggests_the_near_miss(repo):
    write, run = repo
    write("bad.py", "from app.engine import Engin\n")
    assert "did you mean 'Engine'" in run("bad.py", only=["R001"])[0].message


def test_r001_is_silent_on_correct_imports(repo):
    write, run = repo
    write("good.py", "from app.engine import Engine, helper\nimport os\nimport json\n")
    assert run("good.py", only=["R001"]) == []


def test_r001_allows_importing_a_submodule_by_name(repo):
    """`from pkg import submodule` binds a module, not a name in __init__."""
    write, run = repo
    write("good.py", "from app import engine\n")
    assert run("good.py", only=["R001"]) == []


def test_r001_ignores_third_party_and_stdlib(repo):
    write, run = repo
    write("good.py", "from cryptography.hazmat.primitives import hashes\nfrom os import sep\n")
    assert run("good.py", only=["R001"]) == []


# -- R002 ---------------------------------------------------------------------


def test_r002_flags_an_attribute_the_class_lacks(repo):
    write, run = repo
    write("bad.py",
          "from app.engine import Engine\n"
          "def go():\n"
          "    e = Engine()\n"
          "    return e.reconstruct()\n")
    findings = run("bad.py", only=["R002"])
    assert len(findings) == 1
    assert "has no attribute 'reconstruct'" in findings[0].message


def test_r002_is_silent_on_real_attributes(repo):
    write, run = repo
    write("good.py",
          "from app.engine import Engine\n"
          "def go():\n"
          "    e = Engine()\n"
          "    return e.run(), e.items\n")
    assert run("good.py", only=["R002"]) == []


def test_r002_says_nothing_about_a_function_return_value(repo):
    """`x = helper(...)` binds a return value of unknown type. Staying quiet
    here is what kept 90 false positives out of the real tree."""
    write, run = repo
    write("quiet.py",
          "from app.engine import helper\n"
          "def go():\n"
          "    result = helper(1)\n"
          "    return result.anything.at.all\n")
    assert run("quiet.py", only=["R002"]) == []


def test_r002_reports_the_available_attributes_as_evidence(repo):
    write, run = repo
    write("bad.py",
          "from app.engine import Engine\n"
          "def go():\n"
          "    e = Engine()\n"
          "    return e.nope\n")
    assert "run" in run("bad.py", only=["R002"])[0].evidence


# -- R003 ---------------------------------------------------------------------


def test_r003_flags_a_swallowed_exception(repo):
    write, run = repo
    write("bad.py",
          "def go():\n"
          "    try:\n"
          "        return risky()\n"
          "    except Exception:\n"
          "        return 'ok'\n")
    findings = run("bad.py", only=["R003"])
    assert len(findings) == 1
    assert findings[0].severity == "high"


def test_r003_accepts_an_honest_failure_report(repo):
    """Returning {"error": ...} is reporting the failure, not hiding it."""
    write, run = repo
    write("good.py",
          "def go():\n"
          "    try:\n"
          "        return risky()\n"
          "    except Exception as exc:\n"
          "        return {'error': str(exc)}\n")
    assert run("good.py", only=["R003"]) == []


def test_r003_accepts_a_reraise(repo):
    write, run = repo
    write("good.py",
          "def go():\n"
          "    try:\n"
          "        return risky()\n"
          "    except Exception:\n"
          "        raise\n")
    assert run("good.py", only=["R003"]) == []


def test_r003_accepts_logging(repo):
    write, run = repo
    write("good.py",
          "def go(logger):\n"
          "    try:\n"
          "        return risky()\n"
          "    except Exception as exc:\n"
          "        logger.exception(exc)\n"
          "        return None\n")
    assert run("good.py", only=["R003"]) == []


def test_r003_honours_an_explicit_noqa_opt_out(repo):
    """This codebase already writes `# noqa: BLE001 - <reason>`; a checker
    that cannot be told 'yes, deliberately' gets disabled wholesale."""
    write, run = repo
    write("good.py",
          "def go():\n"
          "    try:\n"
          "        return risky()\n"
          "    except Exception:  # noqa: BLE001 - a diagnostic must never raise\n"
          "        return 'degraded'\n")
    assert run("good.py", only=["R003"]) == []


def test_r003_ignores_narrow_exception_types(repo):
    write, run = repo
    write("good.py",
          "def go():\n"
          "    try:\n"
          "        return risky()\n"
          "    except ValueError:\n"
          "        return 'default'\n")
    assert run("good.py", only=["R003"]) == []


# -- R004 ---------------------------------------------------------------------


def test_r004_flags_a_guard_that_always_passes(repo):
    write, run = repo
    write("bad.py",
          "def verify_signature(payload, signature, secret):\n"
          "    return True\n")
    findings = run("bad.py", only=["R004"])
    assert len(findings) == 1
    assert findings[0].severity == "critical"
    assert "authorises everything" in findings[0].message


def test_r004_flags_it_through_a_docstring(repo):
    write, run = repo
    write("bad.py",
          "def validate_token(token):\n"
          "    '''Placeholder - real implementation needs crypto access.'''\n"
          "    return True\n")
    assert len(run("bad.py", only=["R004"])) == 1


def test_r004_is_silent_on_a_guard_that_can_fail(repo):
    write, run = repo
    write("good.py",
          "def verify_signature(payload, signature, secret):\n"
          "    if not signature:\n"
          "        return False\n"
          "    return payload == secret\n")
    assert run("good.py", only=["R004"]) == []


def test_r004_ignores_non_guard_functions(repo):
    write, run = repo
    write("good.py", "def is_enabled():\n    return True\n")
    assert run("good.py", only=["R004"]) == []


def test_r004_reaches_into_javascript(tmp_path):
    """The known instance of this failure is in the Worker, so the rule has
    to cross the language boundary to be worth anything."""
    (tmp_path / "app").mkdir()
    (tmp_path / "app" / "__init__.py").write_text("", encoding="utf-8")
    worker = tmp_path / "worker" / "utils"
    worker.mkdir(parents=True)
    (worker / "validate.js").write_text(
        "async function verifySignature(payload, signature, secret) {\n"
        "  // HMAC-SHA256 verification\n"
        "  // This is a placeholder - full implementation requires crypto access\n"
        "  return true;\n"
        "}\n",
        encoding="utf-8",
    )
    findings = run_rules(Inspector(tmp_path), only=["R004"])
    assert len(findings) == 1
    assert findings[0].path == "worker/utils/validate.js"


def test_r004_is_silent_on_real_javascript_verification(tmp_path):
    (tmp_path / "app").mkdir()
    (tmp_path / "app" / "__init__.py").write_text("", encoding="utf-8")
    worker = tmp_path / "worker" / "utils"
    worker.mkdir(parents=True)
    (worker / "validate.js").write_text(
        "async function verifySignature(payload, signature, secret) {\n"
        "  const expected = await hmac(payload, secret);\n"
        "  return timingSafeEqual(expected, signature);\n"
        "}\n",
        encoding="utf-8",
    )
    assert run_rules(Inspector(tmp_path), only=["R004"]) == []


# -- R005 ---------------------------------------------------------------------


def _wire(tmp_path, routes: str, cli: str):
    for package, body in (("warnetech_server", routes), ("warnetech_cli", cli)):
        target = tmp_path / package
        target.mkdir(exist_ok=True)
        (target / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "warnetech_server" / "routes.py").write_text(routes, encoding="utf-8")
    (tmp_path / "warnetech_cli" / "commands.py").write_text(cli, encoding="utf-8")
    return run_rules(Inspector(tmp_path), only=["R005"])


def test_r005_flags_a_route_with_no_client(tmp_path):
    findings = _wire(
        tmp_path,
        'def build():\n    router.register("POST", "/tests/run", h)\n',
        'def status(self):\n    return self.client.get("/status")\n',
    )
    assert len(findings) == 1
    assert "/tests/run" in findings[0].message


def test_r005_is_silent_when_the_cli_calls_the_route(tmp_path):
    findings = _wire(
        tmp_path,
        'def build():\n    router.register("GET", "/status", h)\n',
        'def status(self):\n    return self.client.get("/status")\n',
    )
    assert findings == []


# -- curriculum integrity -------------------------------------------------------


def test_every_rule_declares_where_it_was_learned(repo):
    """A rule with no origin has not been learned, only assumed."""
    for rule in RULES:
        assert rule.origin.strip(), f"{rule.id} has no origin"
        assert len(rule.lesson.strip()) > 80, f"{rule.id}'s lesson is too thin to teach anything"
        assert rule.check is not None, f"{rule.id} has no check"


def test_rule_ids_are_unique():
    assert len(RULES_BY_ID) == len(RULES)


def test_findings_are_sorted_most_severe_first(repo):
    write, run = repo
    write("bad.py",
          "from app.engine import missing\n"
          "def verify_it():\n"
          "    return True\n")
    findings = run("bad.py")
    severities = [f.severity for f in findings]
    assert severities == sorted(severities, key=lambda s: {"critical": 0, "high": 1, "medium": 2}[s])


def test_a_clean_file_produces_no_findings_at_all(repo):
    write, run = repo
    write("clean.py",
          "from app.engine import Engine\n"
          "def go():\n"
          "    engine = Engine()\n"
          "    try:\n"
          "        return engine.run()\n"
          "    except ValueError as exc:\n"
          "        return {'error': str(exc)}\n")
    assert run("clean.py") == []


# -- scoping ---------------------------------------------------------------------


def _js_repo(tmp_path):
    (tmp_path / "app").mkdir()
    (tmp_path / "app" / "__init__.py").write_text("", encoding="utf-8")
    worker = tmp_path / "worker" / "utils"
    worker.mkdir(parents=True)
    js = worker / "validate.js"
    js.write_text(
        "async function verifySignature(a, b, c) {\n  // placeholder\n  return true;\n}\n",
        encoding="utf-8",
    )
    return js


def test_whole_tree_run_sweeps_javascript(tmp_path):
    _js_repo(tmp_path)
    assert len(run_rules(Inspector(tmp_path), only=["R004"])) == 1


def test_scoped_run_ignores_javascript_it_was_not_given(tmp_path):
    """A pre-commit run must not report a file the change never touched."""
    _js_repo(tmp_path)
    only_python = [tmp_path / "app" / "__init__.py"]
    assert run_rules(Inspector(tmp_path), only_python, only=["R004"]) == []


def test_scoped_run_still_checks_javascript_it_was_given(tmp_path):
    js = _js_repo(tmp_path)
    assert len(run_rules(Inspector(tmp_path), [js], only=["R004"])) == 1
