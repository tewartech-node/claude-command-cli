"""The inspector must be right about what exists, and honest about what it
cannot know. The tri-state (True / False / None) is the contract under test."""

from __future__ import annotations

import pytest

from warnetech_curriculum.inspector import Inspector


@pytest.fixture
def tree(tmp_path):
    """A miniature first-party package to resolve against."""
    pkg = tmp_path / "demo"
    pkg.mkdir()
    (pkg / "__init__.py").write_text(
        "from .core import Engine\n"
        "VERSION = '1'\n"
        "LOW, MID, HIGH = 'low', 'mid', 'high'\n"
        "__all__ = ['Engine', 'VERSION', 'lazy_thing']\n",
        encoding="utf-8",
    )
    (pkg / "core.py").write_text(
        "class Engine:\n"
        "    LIMIT = 10\n"
        "    def __init__(self):\n"
        "        self.slices = []\n"
        "    def run(self):\n"
        "        return 1\n"
        "\n"
        "def helper():\n"
        "    return 2\n",
        encoding="utf-8",
    )
    (pkg / "opaque.py").write_text("from os.path import *\n", encoding="utf-8")
    (pkg / "dynamic.py").write_text(
        "class Bag:\n"
        "    def __getattr__(self, name):\n"
        "        return None\n",
        encoding="utf-8",
    )
    (pkg / "derived.py").write_text(
        "from .core import Engine\n"
        "class Turbo(Engine):\n"
        "    def boost(self):\n"
        "        return 3\n",
        encoding="utf-8",
    )
    return Inspector(tmp_path)


def test_discovers_first_party_packages(tree):
    assert tree.first_party == {"demo"}
    assert tree.is_first_party("demo.core") is True
    assert tree.is_first_party("os.path") is False


def test_module_path_resolves_modules_and_packages(tree):
    assert tree.module_path("demo").name == "__init__.py"
    assert tree.module_path("demo.core").name == "core.py"
    assert tree.module_path("demo.missing") is None


def test_module_name_round_trips(tree):
    assert tree.module_name_for(tree.module_path("demo.core")) == "demo.core"
    assert tree.module_name_for(tree.module_path("demo")) == "demo"


def test_missing_first_party_module_is_a_definite_no(tree):
    surface = tree.module_surface("demo.nope")
    assert surface.exists is False
    assert surface.exports("anything") is False


def test_third_party_is_opaque_not_missing(tree):
    """Out of scope is not the same as absent; never flag stdlib imports."""
    surface = tree.module_surface("os.path")
    assert surface.exists is True
    assert surface.exports("join") is None


def test_top_level_bindings_are_all_collected(tree):
    surface = tree.module_surface("demo")
    for name in ("Engine", "VERSION", "LOW", "MID", "HIGH", "lazy_thing"):
        assert surface.exports(name) is True, name


def test_tuple_unpacking_binds_every_name(tree):
    """`A, B, C = ...` binds three names. Missing this invents false positives."""
    surface = tree.module_surface("demo")
    assert surface.exports("MID") is True


def test_absent_symbol_is_reported(tree):
    assert tree.module_surface("demo").exports("nonexistent") is False


def test_star_import_makes_a_module_opaque(tree):
    surface = tree.module_surface("demo.opaque")
    assert surface.opaque is True
    assert surface.exports("anything") is None


def test_class_surface_sees_methods_and_self_assignments(tree):
    surface = tree.class_surface("demo.core", "Engine")
    assert surface.has("run") is True
    assert surface.has("slices") is True
    assert surface.has("LIMIT") is True
    assert surface.has("reconstruct") is False


def test_getattr_class_is_opaque(tree):
    assert tree.class_surface("demo.dynamic", "Bag").has("whatever") is None


def test_inherited_class_is_opaque(tree):
    """Turbo's real surface includes Engine's, so refuse to answer."""
    surface = tree.class_surface("demo.derived", "Turbo")
    assert surface.opaque is True
    assert surface.has("anything") is None


def test_missing_class_is_a_definite_no(tree):
    assert tree.class_surface("demo.core", "Nonexistent").exists is False


def test_relative_imports_resolve_against_the_package(tree):
    found = tree.imports_in(tree.module_path("demo.derived"))
    assert ("demo.core", "Engine", 1) in found


def test_relative_import_in_package_init_resolves(tree):
    found = tree.imports_in(tree.module_path("demo"))
    assert ("demo.core", "Engine", 1) in found


def test_star_imports_are_not_reported_as_symbols(tree):
    assert tree.imports_in(tree.module_path("demo.opaque")) == []


def test_unparseable_file_is_opaque_not_missing(tree, tmp_path):
    (tmp_path / "demo" / "broken.py").write_text("def (:\n", encoding="utf-8")
    surface = tree.module_surface("demo.broken")
    assert surface.exists is True and surface.opaque is True


def test_source_files_skips_pycache(tree, tmp_path):
    cache = tmp_path / "demo" / "__pycache__"
    cache.mkdir()
    (cache / "core.cpython-311.pyc.py").write_text("x = 1\n", encoding="utf-8")
    assert all("__pycache__" not in p.parts for p in tree.source_files())
