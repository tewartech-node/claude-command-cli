"""Tests for warnetech_cli.main.error_hint and its wiring into main()'s
top-level exception handler.

error_hint() only recognises specific, previously-seen failure shapes and
returns None for anything else -- a wrong guess at "what to do" is worse
than no guess, so the "unrecognised exception gets no hint" case is tested
as deliberately, not incidentally, as the recognised ones.
"""

from __future__ import annotations

import sys


from warnetech_cli.main import error_hint, main

# warnetech_cli/__init__.py does `from .main import main`, which rebinds the
# `main` attribute on the *package* object to the function -- so
# `warnetech_cli.main` (attribute access) resolves to the function, not the
# submodule, and a string-path monkeypatch.setattr("warnetech_cli.main.X", ...)
# would resolve against the wrong object. sys.modules keeps the real
# submodule reachable regardless; use that directly.
_main_module = sys.modules["warnetech_cli.main"]


def test_module_not_found_gets_the_doctor_hint():
    hint = error_hint(ModuleNotFoundError("No module named 'boto3'"))
    assert hint is not None
    assert "warnetech-doctor" in hint


def test_import_error_with_the_same_message_shape_also_matches():
    """Some code raises a plain ImportError with the same "No module named"
    text rather than the ModuleNotFoundError subclass; the hint should not
    depend on which one was used."""
    hint = error_hint(ImportError("No module named 'lz4'"))
    assert hint is not None
    assert "warnetech-doctor" in hint


def test_connection_error_gets_the_server_hint():
    hint = error_hint(ConnectionError("Connection refused"))
    assert hint is not None
    assert "server-ping" in hint


def test_timeout_error_gets_the_server_hint():
    assert error_hint(TimeoutError("timed out")) is not None


def test_file_not_found_names_the_file():
    hint = error_hint(FileNotFoundError("config.json"))
    assert hint is not None
    assert "config.json" in hint


def test_an_unrecognised_exception_gets_no_hint():
    """The important negative case: a wrong guess is worse than none."""
    assert error_hint(ValueError("something unrelated broke")) is None


def test_a_plain_runtime_error_gets_no_hint():
    assert error_hint(RuntimeError("some internal invariant failed")) is None


# -- wiring into main() ------------------------------------------------------


class _ExplodingCommands:
    def __init__(self, config):
        pass

    def status(self, args=None):
        raise ModuleNotFoundError("No module named 'boto3'")


def test_main_prints_the_hint_to_stderr_for_a_recognised_failure(monkeypatch, capsys):
    monkeypatch.setattr(_main_module, "Commands", _ExplodingCommands)
    code = main(["status"])
    assert code == 1
    err = capsys.readouterr().err
    assert "warnetech-doctor" in err


class _DifferentlyExplodingCommands:
    def __init__(self, config):
        pass

    def status(self, args=None):
        raise ValueError("something unrelated broke")


def test_main_prints_just_the_error_when_no_hint_applies(monkeypatch, capsys):
    monkeypatch.setattr(_main_module, "Commands", _DifferentlyExplodingCommands)
    code = main(["status"])
    assert code == 1
    err = capsys.readouterr().err
    assert "something unrelated broke" in err
    assert "->" not in err
