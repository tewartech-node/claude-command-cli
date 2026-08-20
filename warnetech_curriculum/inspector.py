"""Static introspection of the codebase, using the building language itself.

This module answers one question: *does the thing this code refers to
actually exist?* It answers it with `ast` from the standard library, and
nothing else -- no model, no parameters, no API key, no network, no
third-party parser. On Termux that matters twice over: it works offline,
and it works on a device with no room for a toolchain.

Crucially it answers **without importing anything**. `importlib` would run
module-level code as a side effect of asking a question about it, and a
checker that executes the code it is judging is not safe to run before an
action -- which is exactly when it needs to run. So module resolution here
is pure path arithmetic over the repository tree, and symbol resolution is
a parse of the target file. Asking "does `warnetech_envelope` export
`open`?" costs one file read and one parse, and changes nothing.

Where certainty is not available -- a star-import, an unresolvable base
class, a dynamic `__getattr__` -- the surface is marked *opaque* and the
caller is expected to stay silent rather than guess. A checker that cries
wolf gets switched off, and a switched-off checker protects nothing.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import List, Optional, Set, Tuple


@dataclass
class ModuleSurface:
    """What a module binds at top level, as far as can be proven statically."""

    module: str
    path: Optional[Path]
    exists: bool
    names: Set[str] = field(default_factory=set)
    opaque: bool = False
    opaque_reason: str = ""

    def exports(self, symbol: str) -> Optional[bool]:
        """True / False / None, where None means "cannot be proven either way".

        The tri-state is the whole discipline of this module: an honest
        "I don't know" is a supported answer, and callers must handle it.
        """
        if not self.exists:
            return False
        if self.opaque:
            return None
        return symbol in self.names


@dataclass
class ClassSurface:
    """The attribute surface of a class: its methods plus whatever `__init__`
    and friends assign onto `self`."""

    module: str
    name: str
    exists: bool
    attributes: Set[str] = field(default_factory=set)
    opaque: bool = False
    opaque_reason: str = ""

    def has(self, attribute: str) -> Optional[bool]:
        if not self.exists:
            return False
        if self.opaque:
            return None
        return attribute in self.attributes


class Inspector:
    """Resolves modules and symbols against a repository tree.

    `root` is the repository root. Any top-level directory containing an
    `__init__.py` is treated as first-party; everything else (stdlib,
    site-packages) is deliberately out of scope, because this package's job
    is to police *our* wiring, not to re-implement a type checker.
    """

    def __init__(self, root: Path) -> None:
        self.root = Path(root).resolve()

    # -- first-party topology --------------------------------------------

    @property
    @lru_cache(maxsize=1)
    def first_party(self) -> Set[str]:  # type: ignore[misc]
        return {
            child.name
            for child in self.root.iterdir()
            if child.is_dir() and (child / "__init__.py").exists()
        }

    def is_first_party(self, module: str) -> bool:
        return module.split(".", 1)[0] in self.first_party

    def module_path(self, module: str) -> Optional[Path]:
        """Map a dotted module name onto a file, without importing it."""
        parts = module.split(".")
        if not parts or parts[0] not in self.first_party:
            return None
        base = self.root.joinpath(*parts)
        for candidate in (base.with_suffix(".py"), base / "__init__.py"):
            if candidate.is_file():
                return candidate
        return None

    def module_name_for(self, path: Path) -> Optional[str]:
        """Inverse of module_path: which module does this file define?"""
        try:
            rel = Path(path).resolve().relative_to(self.root)
        except ValueError:
            return None
        parts = list(rel.parts)
        if not parts or parts[0] not in self.first_party:
            return None
        if parts[-1] == "__init__.py":
            parts = parts[:-1]
        elif parts[-1].endswith(".py"):
            parts[-1] = parts[-1][:-3]
        else:
            return None
        return ".".join(parts)

    # -- parsing ----------------------------------------------------------

    def parse(self, path: Path) -> Optional[ast.Module]:
        try:
            return ast.parse(Path(path).read_text(encoding="utf-8"), filename=str(path))
        except (OSError, SyntaxError):
            return None

    # -- module surface ---------------------------------------------------

    def module_surface(self, module: str) -> ModuleSurface:
        path = self.module_path(module)
        if path is None:
            # Not first-party, or genuinely absent. Distinguish the two:
            # only a missing *first-party* module is a finding.
            if not self.is_first_party(module):
                return ModuleSurface(
                    module, None, exists=True, opaque=True, opaque_reason="not first-party"
                )
            return ModuleSurface(module, None, exists=False)

        tree = self.parse(path)
        if tree is None:
            return ModuleSurface(
                module, path, exists=True, opaque=True, opaque_reason="file could not be parsed"
            )

        names: Set[str] = set()
        opaque_reason = ""
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                names.add(node.name)
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    names |= self._bound_names(target)
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                names.add(node.target.id)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    names.add(alias.asname or alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    if alias.name == "*":
                        # A star-import can bind anything. Refuse to guess.
                        opaque_reason = f"star-import from {node.module or '.'}"
                        continue
                    names.add(alias.asname or alias.name)

        # __all__ is a promise about the public surface; honour it as an
        # additional source of names (a module may re-export lazily).
        names |= self._dunder_all(tree)

        return ModuleSurface(
            module, path, exists=True, names=names,
            opaque=bool(opaque_reason), opaque_reason=opaque_reason,
        )

    @classmethod
    def _bound_names(cls, target: ast.expr) -> Set[str]:
        """Names bound by one assignment target.

        Handles tuple and list unpacking (`A, B, C = ...`) and starred
        targets, not just the plain `X = ...` case. Missing this is exactly
        how a checker invents a false positive: the name is bound, the
        checker just could not see the shape that bound it.
        """
        if isinstance(target, ast.Name):
            return {target.id}
        if isinstance(target, (ast.Tuple, ast.List)):
            found: Set[str] = set()
            for element in target.elts:
                found |= cls._bound_names(element)
            return found
        if isinstance(target, ast.Starred):
            return cls._bound_names(target.value)
        return set()

    @staticmethod
    def _dunder_all(tree: ast.Module) -> Set[str]:
        out: Set[str] = set()
        for node in tree.body:
            targets = node.targets if isinstance(node, ast.Assign) else []
            if not any(isinstance(t, ast.Name) and t.id == "__all__" for t in targets):
                continue
            value = node.value
            if isinstance(value, (ast.List, ast.Tuple)):
                for element in value.elts:
                    if isinstance(element, ast.Constant) and isinstance(element.value, str):
                        out.add(element.value)
        return out

    # -- class surface ----------------------------------------------------

    def class_surface(self, module: str, class_name: str) -> ClassSurface:
        path = self.module_path(module)
        if path is None:
            return ClassSurface(module, class_name, exists=False)
        tree = self.parse(path)
        if tree is None:
            return ClassSurface(
                module, class_name, exists=False, opaque=True, opaque_reason="unparseable"
            )

        node = next(
            (n for n in ast.walk(tree) if isinstance(n, ast.ClassDef) and n.name == class_name),
            None,
        )
        if node is None:
            return ClassSurface(module, class_name, exists=False)

        # Inheritance from anything we cannot follow means the real surface
        # is larger than what we can see. Stay quiet rather than guess.
        for base in node.bases:
            label = ast.unparse(base) if hasattr(ast, "unparse") else ""
            if label not in ("object", ""):
                return ClassSurface(
                    module, class_name, exists=True, opaque=True,
                    opaque_reason=f"inherits from {label}",
                )

        attributes: Set[str] = set()
        for child in node.body:
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                attributes.add(child.name)
                if child.name in ("__getattr__", "__getattribute__"):
                    return ClassSurface(
                        module, class_name, exists=True, opaque=True,
                        opaque_reason=f"defines {child.name}",
                    )
                attributes |= self._self_assignments(child)
            elif isinstance(child, ast.Assign):
                for target in child.targets:
                    if isinstance(target, ast.Name):
                        attributes.add(target.id)
            elif isinstance(child, ast.AnnAssign) and isinstance(child.target, ast.Name):
                attributes.add(child.target.id)

        return ClassSurface(module, class_name, exists=True, attributes=attributes)

    @staticmethod
    def _self_assignments(func: ast.AST) -> Set[str]:
        found: Set[str] = set()
        for node in ast.walk(func):
            targets: List[ast.expr] = []
            if isinstance(node, ast.Assign):
                targets = list(node.targets)
            elif isinstance(node, (ast.AnnAssign, ast.AugAssign)):
                targets = [node.target]
            for target in targets:
                if (
                    isinstance(target, ast.Attribute)
                    and isinstance(target.value, ast.Name)
                    and target.value.id == "self"
                ):
                    found.add(target.attr)
        return found

    # -- import extraction -------------------------------------------------

    def imports_in(self, path: Path) -> List[Tuple[str, Optional[str], int]]:
        """Every import in a file as (module, symbol_or_None, lineno).

        Relative imports are resolved against the file's own package, so
        `from .database import X` inside warnetech_ai_controller/controller.py
        comes back as ("warnetech_ai_controller.database", "X", lineno).
        """
        tree = self.parse(path)
        if tree is None:
            return []
        current = self.module_name_for(path) or ""
        package = current.rsplit(".", 1)[0] if "." in current else current
        # A package's __init__.py is its own package for relative purposes.
        if self.module_path(current) and self.module_path(current).name == "__init__.py":
            package = current

        out: List[Tuple[str, Optional[str], int]] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    out.append((alias.name, None, node.lineno))
            elif isinstance(node, ast.ImportFrom):
                module = self._resolve_relative(node, package)
                if module is None:
                    continue
                for alias in node.names:
                    if alias.name == "*":
                        continue
                    out.append((module, alias.name, node.lineno))
        return out

    @staticmethod
    def _resolve_relative(node: ast.ImportFrom, package: str) -> Optional[str]:
        if not node.level:
            return node.module
        parts = package.split(".") if package else []
        # level 1 == current package; each extra level walks one step up.
        climb = node.level - 1
        if climb > len(parts):
            return None
        base = parts[: len(parts) - climb] if climb else parts
        if node.module:
            base = base + node.module.split(".")
        return ".".join(base) if base else None

    def source_files(self, packages: Optional[List[str]] = None) -> List[Path]:
        """Every first-party .py file, tests excluded -- tests deliberately
        poke at things that do not exist."""
        targets = packages or sorted(self.first_party)
        files: List[Path] = []
        for package in targets:
            base = self.root / package
            if base.is_dir():
                files.extend(sorted(p for p in base.rglob("*.py") if "__pycache__" not in p.parts))
        return files
