"""The enforced curriculum: one rule per lesson this repository paid for.

Every rule here exists because something in *this* codebase actually broke
in that exact way. The `origin` field is not decoration -- it is the commit
you can go read. A rule with no origin has not been learned, it has been
assumed, and assumptions are what the curriculum exists to eliminate.

All checks are deterministic functions of the source tree. Same tree, same
findings, every time, on any machine, offline. There is no model here and
no threshold to tune: a rule either proves a defect or stays silent.

Adding a rule is deliberately a two-step act -- record the failure in the
ledger first, then write the rule that would have caught it. That ordering
is the point. It keeps the curriculum honest: enforcement always traces
back to evidence.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional, Set

from .inspector import Inspector

CRITICAL, HIGH, MEDIUM, LOW = "critical", "high", "medium", "low"
SEVERITY_ORDER = {CRITICAL: 0, HIGH: 1, MEDIUM: 2, LOW: 3}


@dataclass(frozen=True)
class Finding:
    rule: str
    severity: str
    path: str
    line: int
    message: str
    evidence: str = ""

    def to_dict(self) -> Dict[str, object]:
        return {
            "rule": self.rule,
            "severity": self.severity,
            "path": self.path,
            "line": self.line,
            "message": self.message,
            "evidence": self.evidence,
        }

    def render(self) -> str:
        return f"{self.path}:{self.line}: [{self.severity}] {self.rule} {self.message}"


@dataclass
class Rule:
    id: str
    title: str
    severity: str
    origin: str
    lesson: str
    check: Callable[["RuleContext"], List[Finding]] = field(repr=False, default=None)  # type: ignore
    enabled: bool = True


@dataclass
class RuleContext:
    """Everything a check may look at. Passed in rather than reached for, so
    a rule cannot quietly acquire a dependency on the network or the clock."""

    inspector: Inspector
    files: List[Path]
    # True when the caller handed us an explicit file list (a pre-commit or
    # CI run). Rules that would otherwise sweep the whole repository must
    # narrow themselves, or they report files the change never touched.
    scoped: bool = False

    def relative(self, path: Path) -> str:
        try:
            return str(Path(path).resolve().relative_to(self.inspector.root))
        except ValueError:
            return str(path)


# -- helpers ------------------------------------------------------------------


def _suppressed(path: Path, line: int, token: str) -> bool:
    """Honour an explicit, commented opt-out on the offending line.

    This codebase already writes `# noqa: BLE001 - a diagnostic must never
    raise`, and that is a real engineering decision with a stated reason.
    A curriculum that cannot be told "yes, on purpose, here is why" trains
    people to disable it wholesale.
    """
    try:
        lines = Path(path).read_text(encoding="utf-8").splitlines()
    except OSError:
        return False
    if not (1 <= line <= len(lines)):
        return False
    return token in lines[line - 1]


def _import_map(inspector: Inspector, path: Path) -> Dict[str, tuple]:
    """local name -> (module, original symbol) for first-party imports."""
    out: Dict[str, tuple] = {}
    for module, symbol, _ in inspector.imports_in(path):
        if symbol and inspector.is_first_party(module):
            out[symbol] = (module, symbol)
    return out


# -- R001 ---------------------------------------------------------------------


def check_unresolved_import(ctx: RuleContext) -> List[Finding]:
    """Every first-party import must resolve to something that exists."""
    findings: List[Finding] = []
    for path in ctx.files:
        for module, symbol, line in ctx.inspector.imports_in(path):
            if not ctx.inspector.is_first_party(module):
                continue
            surface = ctx.inspector.module_surface(module)
            if not surface.exists:
                findings.append(
                    Finding(
                        "R001", CRITICAL, ctx.relative(path), line,
                        f"imports module '{module}', which does not exist",
                        evidence=f"no file for {module} under {ctx.inspector.root.name}/",
                    )
                )
                continue
            if symbol is None:
                continue
            # `from pkg import submodule` binds a module, not a top-level
            # name in pkg/__init__.py. Resolve that before calling it missing.
            if ctx.inspector.module_path(f"{module}.{symbol}") is not None:
                continue
            exported = surface.exports(symbol)
            if exported is False:
                near = _nearest(symbol, surface.names)
                hint = f"; did you mean '{near}'?" if near else ""
                findings.append(
                    Finding(
                        "R001", CRITICAL, ctx.relative(path), line,
                        f"imports '{symbol}' from '{module}', which does not export it{hint}",
                        evidence=f"{module} exports: {', '.join(sorted(surface.names)[:12])}",
                    )
                )
    return findings


def _nearest(name: str, candidates: Set[str]) -> Optional[str]:
    """Cheap edit-distance suggestion. Pure string arithmetic -- no model."""
    import difflib

    matches = difflib.get_close_matches(name, sorted(candidates), n=1, cutoff=0.6)
    return matches[0] if matches else None


# -- R002 ---------------------------------------------------------------------


def check_unknown_attribute(ctx: RuleContext) -> List[Finding]:
    """An attribute read off a locally-constructed first-party class must be
    an attribute that class actually has."""
    findings: List[Finding] = []
    for path in ctx.files:
        tree = ctx.inspector.parse(path)
        if tree is None:
            continue
        imports = _import_map(ctx.inspector, path)
        if not imports:
            continue
        for func in [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]:
            bound: Dict[str, tuple] = {}
            for node in ast.walk(func):
                # local = SomeFirstPartyClass(...)
                if (
                    isinstance(node, ast.Assign)
                    and isinstance(node.value, ast.Call)
                    and isinstance(node.value.func, ast.Name)
                    and node.value.func.id in imports
                    and len(node.targets) == 1
                    and isinstance(node.targets[0], ast.Name)
                ):
                    bound[node.targets[0].id] = imports[node.value.func.id]
            for node in ast.walk(func):
                if (
                    isinstance(node, ast.Attribute)
                    and isinstance(node.value, ast.Name)
                    and node.value.id in bound
                ):
                    module, class_name = bound[node.value.id]
                    surface = ctx.inspector.class_surface(module, class_name)
                    # Only a real class tells us anything. If the imported
                    # name is a function, `x = f(...)` binds its *return
                    # value*, whose type we cannot know statically -- so
                    # stay silent rather than invent a shape for it.
                    if surface.exists and surface.has(node.attr) is False:
                        near = _nearest(node.attr, surface.attributes)
                        hint = f"; did you mean '{near}'?" if near else ""
                        findings.append(
                            Finding(
                                "R002", CRITICAL, ctx.relative(path), node.lineno,
                                f"'{class_name}' has no attribute '{node.attr}'{hint}",
                                evidence=(
                                    f"{class_name} provides: "
                                    f"{', '.join(sorted(a for a in surface.attributes if not a.startswith('_'))[:12])}"
                                ),
                            )
                        )
    return findings


# -- R003 ---------------------------------------------------------------------


def check_silent_failure(ctx: RuleContext) -> List[Finding]:
    """A broad `except` that returns normally, never re-raises and never logs,
    converts a failure into a plausible-looking success."""
    findings: List[Finding] = []
    for path in ctx.files:
        tree = ctx.inspector.parse(path)
        if tree is None:
            continue
        for handler in [n for n in ast.walk(tree) if isinstance(n, ast.ExceptHandler)]:
            if not _is_broad(handler):
                continue
            if _suppressed(path, handler.lineno, "noqa: BLE001"):
                continue
            body = list(ast.walk(handler))
            if any(isinstance(n, ast.Raise) for n in body):
                continue
            if any(
                isinstance(n, ast.Call)
                and "log" in (ast.unparse(n.func) if hasattr(ast, "unparse") else "").lower()
                for n in body
            ):
                continue
            returns = [n for n in body if isinstance(n, ast.Return) and n.value is not None]
            if not returns:
                continue
            if any(_carries_failure_flag(r.value) for r in returns):
                continue
            findings.append(
                Finding(
                    "R003", HIGH, ctx.relative(path), handler.lineno,
                    "broad except returns a value without re-raising, logging, or "
                    "flagging failure -- the caller cannot tell this went wrong",
                    evidence="add `raise`, log it, return an ok/error flag, or "
                             "mark it `# noqa: BLE001 - <reason>`",
                )
            )
    return findings


def _is_broad(handler: ast.ExceptHandler) -> bool:
    if handler.type is None:
        return True
    return isinstance(handler.type, ast.Name) and handler.type.id in ("Exception", "BaseException")


def _carries_failure_flag(value: ast.expr) -> bool:
    """A returned dict saying {"ok": False} / {"error": ...} is an honest
    failure report, not a swallowed one."""
    if isinstance(value, ast.Dict):
        for key in value.keys:
            if isinstance(key, ast.Constant) and str(key.value).lower() in (
                "ok", "error", "status", "success", "failed"
            ):
                return True
    if isinstance(value, ast.Constant) and value.value in (False, None):
        return True
    return False


# -- R004 ---------------------------------------------------------------------

_GUARD_NAME = re.compile(r"(verify|validate|check|authent|authoriz|is_valid|ensure)", re.I)
_JS_ALWAYS_TRUE = re.compile(
    r"(?:async\s+)?function\s+(\w*(?:verify|validate|check|authent|authoriz)\w*)"
    r"\s*\([^)]*\)\s*\{(?P<body>(?:[^{}]|\{[^{}]*\})*?)\}",
    re.I | re.S,
)


def check_verification_stub(ctx: RuleContext) -> List[Finding]:
    """A security guard that cannot fail is not a guard."""
    findings: List[Finding] = []
    for path in ctx.files:
        tree = ctx.inspector.parse(path)
        if tree is None:
            continue
        for func in [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]:
            if not _GUARD_NAME.search(func.name):
                continue
            body = [n for n in func.body if not _is_docstring(n)]
            if len(body) == 1 and isinstance(body[0], ast.Return):
                value = body[0].value
                if isinstance(value, ast.Constant) and value.value is True:
                    findings.append(
                        Finding(
                            "R004", CRITICAL, ctx.relative(path), func.lineno,
                            f"'{func.name}' always returns True -- it authorises everything",
                            evidence="a guard whose only statement is `return True` "
                                     "passes forged input as readily as genuine input",
                        )
                    )
    findings.extend(_check_js_stubs(ctx))
    return findings


def _is_docstring(node: ast.stmt) -> bool:
    return isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str)


def _check_js_stubs(ctx: RuleContext) -> List[Finding]:
    """The known instance of this failure is in JavaScript, so the rule has
    to reach there too. Regex rather than a parser: deliberately narrow,
    matching only a guard whose body is comments plus `return true`."""
    findings: List[Finding] = []
    root = ctx.inspector.root
    if ctx.scoped:
        candidates = [p for p in ctx.files if p.suffix == ".js"]
    else:
        candidates = sorted(root.glob("worker/**/*.js")) + sorted(root.glob("warnetech_cli_legacy/*"))
    for path in candidates:
        if path.is_dir() or path.suffix not in (".js", ""):
            continue
        try:
            source = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for match in _JS_ALWAYS_TRUE.finditer(source):
            body = match.group("body")
            stripped = re.sub(r"//[^\n]*|/\*.*?\*/", "", body, flags=re.S).strip()
            if stripped.rstrip(";") == "return true":
                line = source[: match.start()].count("\n") + 1
                findings.append(
                    Finding(
                        "R004", CRITICAL,
                        str(path.resolve().relative_to(root)), line,
                        f"'{match.group(1)}' always returns true -- it authorises everything",
                        evidence="body is comments plus `return true`",
                    )
                )
    return findings


# -- R005 ---------------------------------------------------------------------

_ROUTE_RE = re.compile(r"""register\(\s*["'](?P<method>[A-Z]+)["']\s*,\s*["'](?P<path>/[^"']*)["']""")


def check_orphaned_route(ctx: RuleContext) -> List[Finding]:
    """A registered server route with no client is a surface nobody can reach."""
    findings: List[Finding] = []
    root = ctx.inspector.root
    routes_file = root / "warnetech_server" / "routes.py"
    if not routes_file.is_file():
        return findings
    try:
        source = routes_file.read_text(encoding="utf-8")
    except OSError:
        return findings

    consumers = ""
    for package in ("warnetech_cli", "warnetech_operator"):
        for path in sorted((root / package).rglob("*.py")) if (root / package).is_dir() else []:
            try:
                consumers += path.read_text(encoding="utf-8")
            except OSError:
                continue

    for match in _ROUTE_RE.finditer(source):
        route = match.group("path")
        if f'"{route}"' in consumers or f"'{route}'" in consumers:
            continue
        line = source[: match.start()].count("\n") + 1
        findings.append(
            Finding(
                "R005", MEDIUM, "warnetech_server/routes.py", line,
                f"route {match.group('method')} {route} has no caller in the CLI layer",
                evidence="registered on the server but unreachable from warnetech_cli/",
            )
        )
    return findings


# -- the curriculum -----------------------------------------------------------

RULES: List[Rule] = [
    Rule(
        id="R001",
        title="imports must resolve",
        severity=CRITICAL,
        origin="f0b7781, c0bf30c, 5c33780, 1b1477c",
        lesson=(
            "warnetech_ai_controller/diagnostics.py was written against an API that was "
            "imagined rather than read: `from warnetech_envelope import open` (the export "
            "is `unseal`) and `from supabase_schema.database import get_client` (no such "
            "module). Earlier, commit 1b1477c fixed a wrong PBKDF2 import that had silently "
            "disabled all CLI encryption. Both were one parse away from being obvious."
        ),
        check=check_unresolved_import,
    ),
    Rule(
        id="R002",
        title="attributes must exist on the class",
        severity=CRITICAL,
        origin="f0b7781",
        lesson=(
            "The same module read RetentionEngine().slices and called GhostEngine()"
            ".reconstruct(). Neither exists. The class was never opened; its shape was "
            "assumed from its name."
        ),
        check=check_unknown_attribute,
    ),
    Rule(
        id="R003",
        title="failures must stay visible",
        severity=HIGH,
        origin="f0b7781",
        lesson=(
            "Every check in that module caught its own exception and returned the error as "
            "a string, so `warnetech ai-diagnose` reported success while every single check "
            "was failing. Swallowing an exception does not remove the failure, it removes "
            "your ability to see it."
        ),
        check=check_silent_failure,
    ),
    Rule(
        id="R004",
        title="a guard must be able to fail",
        severity=CRITICAL,
        origin="worker/utils/validate.js:146",
        lesson=(
            "verifySignature() in the Worker returns true unconditionally, and "
            "antiTamperCheck() calls it -- so the anti-tamper path passes forged requests. "
            "Its sibling decryptRequest() had the mirror-image bug (it always threw) and "
            "was fixed; this half was left. A stub that fails closed gets found in minutes; "
            "one that fails open can sit for months."
        ),
        check=check_verification_stub,
    ),
    Rule(
        id="R005",
        title="declared surface must be reachable",
        severity=MEDIUM,
        origin="repo scan 2026-08-20",
        lesson=(
            "POST /tests/run and GET /tests/results are registered in the server router with "
            "no caller anywhere in the CLI layer. Shipping an endpoint nobody can invoke is "
            "how a system drifts out of being one system."
        ),
        check=check_orphaned_route,
    ),
]

RULES_BY_ID: Dict[str, Rule] = {rule.id: rule for rule in RULES}


def run_rules(
    inspector: Inspector,
    files: Optional[List[Path]] = None,
    *,
    only: Optional[List[str]] = None,
) -> List[Finding]:
    ctx = RuleContext(
        inspector=inspector,
        files=files if files is not None else inspector.source_files(),
        scoped=files is not None,
    )
    findings: List[Finding] = []
    for rule in RULES:
        if not rule.enabled or (only and rule.id not in only):
            continue
        findings.extend(rule.check(ctx))
    findings.sort(key=lambda f: (SEVERITY_ORDER.get(f.severity, 9), f.path, f.line))
    return findings
