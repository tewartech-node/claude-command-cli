"""
Code Analyzer: AST-based Code Introspection
Analyzes code structure, identifies issues, extracts patterns
"""

import ast
import os
from pathlib import Path
from typing import Dict, List, Set, Any, Optional, Tuple
import json


class CodeAnalyzer:
    """Analyzes codebase using AST and static analysis"""

    def __init__(self, repo_root: str = "."):
        self.repo_root = Path(repo_root)
        self.analyzed_files = {}
        self.dependency_graph = {}
        self.issues = []

    def analyze_codebase(self) -> Dict[str, Any]:
        """Analyze entire codebase for issues"""
        py_files = list(self.repo_root.glob("**/*.py"))
        results = {
            "total_files": len(py_files),
            "files_analyzed": 0,
            "total_issues": 0,
            "issues_by_type": {},
            "dependency_graph": {},
            "code_metrics": {},
        }

        for py_file in py_files:
            if "__pycache__" in str(py_file):
                continue

            try:
                file_issues = self.analyze_file(py_file)
                results["files_analyzed"] += 1
                results["total_issues"] += len(file_issues)

                for issue in file_issues:
                    issue_type = issue["type"]
                    results["issues_by_type"][issue_type] = \
                        results["issues_by_type"].get(issue_type, 0) + 1

            except Exception as e:
                results["total_issues"] += 1
                results["issues_by_type"]["parse_error"] = \
                    results["issues_by_type"].get("parse_error", 0) + 1

        return results

    def analyze_file(self, filepath: Path) -> List[Dict[str, Any]]:
        """Analyze a single Python file for issues"""
        issues = []

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                source = f.read()

            tree = ast.parse(source)
            self.analyzed_files[str(filepath)] = source

            # Check for various issues
            issues.extend(self._check_dead_code(tree, filepath))
            issues.extend(self._check_error_handling(tree, filepath))
            issues.extend(self._check_unused_imports(tree, filepath))
            issues.extend(self._check_code_complexity(tree, filepath))
            issues.extend(self._check_security_issues(tree, filepath))
            issues.extend(self._extract_dependencies(tree, filepath))

        except SyntaxError as e:
            issues.append({
                "type": "syntax_error",
                "file": str(filepath),
                "line": e.lineno,
                "message": f"Syntax error: {e.msg}",
                "severity": "CRITICAL",
            })

        return issues

    def _check_dead_code(self, tree: ast.AST, filepath: Path) -> List[Dict[str, Any]]:
        """Find potentially dead code (unreachable, unused functions)"""
        issues = []

        class DeadCodeFinder(ast.NodeVisitor):
            def __init__(self):
                self.functions = {}
                self.used_names = set()

            def visit_FunctionDef(self, node):
                self.functions[node.name] = node.lineno
                self.generic_visit(node)

            def visit_Call(self, node):
                if isinstance(node.func, ast.Name):
                    self.used_names.add(node.func.id)
                self.generic_visit(node)

            def visit_Name(self, node):
                self.used_names.add(node.id)
                self.generic_visit(node)

        finder = DeadCodeFinder()
        finder.visit(tree)

        for func_name, line_no in finder.functions.items():
            if func_name.startswith("_") or func_name in ["__init__", "__str__", "__repr__"]:
                continue
            if func_name not in finder.used_names and not any(
                isinstance(node, ast.Decorator) for node in ast.walk(tree)
            ):
                issues.append({
                    "type": "dead_code",
                    "file": str(filepath),
                    "line": line_no,
                    "message": f"Potentially unused function: {func_name}",
                    "severity": "INFO",
                })

        return issues

    def _check_error_handling(self, tree: ast.AST, filepath: Path) -> List[Dict[str, Any]]:
        """Find bare except clauses and missing error handling"""
        issues = []

        class ErrorHandlerChecker(ast.NodeVisitor):
            def __init__(self):
                self.bare_excepts = []
                self.missing_handlers = []

            def visit_ExceptHandler(self, node):
                if node.type is None:
                    self.bare_excepts.append(node.lineno)
                self.generic_visit(node)

            def visit_Call(self, node):
                # Check for API calls without try/except
                if isinstance(node.func, ast.Attribute):
                    if node.func.attr in ["open", "request", "connect", "execute"]:
                        self.missing_handlers.append(node.lineno)
                self.generic_visit(node)

        checker = ErrorHandlerChecker()
        checker.visit(tree)

        for line in checker.bare_excepts:
            issues.append({
                "type": "bare_except",
                "file": str(filepath),
                "line": line,
                "message": "Bare except clause catches all exceptions including KeyboardInterrupt",
                "severity": "WARNING",
            })

        return issues

    def _check_unused_imports(self, tree: ast.AST, filepath: Path) -> List[Dict[str, Any]]:
        """Find unused imports"""
        issues = []

        class ImportChecker(ast.NodeVisitor):
            def __init__(self):
                self.imports = {}
                self.used = set()

            def visit_Import(self, node):
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name
                    self.imports[name] = node.lineno
                self.generic_visit(node)

            def visit_ImportFrom(self, node):
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name
                    self.imports[name] = node.lineno
                self.generic_visit(node)

            def visit_Name(self, node):
                self.used.add(node.id)
                self.generic_visit(node)

        checker = ImportChecker()
        checker.visit(tree)

        for name, line in checker.imports.items():
            if name not in checker.used and not name.startswith("_"):
                issues.append({
                    "type": "unused_import",
                    "file": str(filepath),
                    "line": line,
                    "message": f"Import '{name}' is never used",
                    "severity": "INFO",
                })

        return issues

    def _check_code_complexity(self, tree: ast.AST, filepath: Path) -> List[Dict[str, Any]]:
        """Check for overly complex functions (McCabe complexity)"""
        issues = []

        class ComplexityChecker(ast.NodeVisitor):
            def __init__(self):
                self.complexity_results = []

            def visit_FunctionDef(self, node):
                complexity = self._calculate_complexity(node)
                if complexity > 10:  # Threshold
                    self.complexity_results.append((node.name, node.lineno, complexity))
                self.generic_visit(node)

            def _calculate_complexity(self, node):
                complexity = 1
                for child in ast.walk(node):
                    if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                        complexity += 1
                    if isinstance(child, ast.BoolOp):
                        complexity += len(child.values) - 1
                return complexity

        checker = ComplexityChecker()
        checker.visit(tree)

        for func_name, line, complexity in checker.complexity_results:
            issues.append({
                "type": "high_complexity",
                "file": str(filepath),
                "line": line,
                "message": f"Function '{func_name}' has complexity {complexity} (threshold: 10)",
                "severity": "WARNING",
            })

        return issues

    def _check_security_issues(self, tree: ast.AST, filepath: Path) -> List[Dict[str, Any]]:
        """Check for common security issues"""
        issues = []

        class SecurityChecker(ast.NodeVisitor):
            def __init__(self):
                self.issues = []

            def visit_Call(self, node):
                # Check for exec/eval
                if isinstance(node.func, ast.Name):
                    if node.func.id in ["exec", "eval", "compile"]:
                        self.issues.append((node.lineno, f"Dangerous function: {node.func.id}()"))

                # Check for os.system
                if isinstance(node.func, ast.Attribute):
                    if node.func.attr == "system" and isinstance(node.func.value, ast.Name):
                        if node.func.value.id == "os":
                            self.issues.append((node.lineno, "Prefer subprocess over os.system()"))

                self.generic_visit(node)

        checker = SecurityChecker()
        checker.visit(tree)

        for line, message in checker.issues:
            issues.append({
                "type": "security_issue",
                "file": str(filepath),
                "line": line,
                "message": message,
                "severity": "CRITICAL",
            })

        return issues

    def _extract_dependencies(self, tree: ast.AST, filepath: Path) -> List[Dict[str, Any]]:
        """Extract module dependencies"""
        issues = []

        class DependencyExtractor(ast.NodeVisitor):
            def __init__(self):
                self.dependencies = set()

            def visit_Import(self, node):
                for alias in node.names:
                    module = alias.name.split(".")[0]
                    self.dependencies.add(module)
                self.generic_visit(node)

            def visit_ImportFrom(self, node):
                if node.module:
                    module = node.module.split(".")[0]
                    self.dependencies.add(module)
                self.generic_visit(node)

        extractor = DependencyExtractor()
        extractor.visit(tree)

        self.dependency_graph[str(filepath)] = list(extractor.dependencies)

        return issues

    def get_function_signatures(self, filepath: Path) -> Dict[str, Any]:
        """Extract function signatures from a file"""
        signatures = {}

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read())

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    args = [arg.arg for arg in node.args.args]
                    signatures[node.name] = {
                        "args": args,
                        "line": node.lineno,
                        "docstring": ast.get_docstring(node),
                    }

        except Exception as e:
            signatures["_error"] = str(e)

        return signatures

    def find_function(self, function_name: str) -> Optional[Tuple[Path, int, str]]:
        """Find a function definition in the codebase"""
        for filepath, source in self.analyzed_files.items():
            try:
                tree = ast.parse(source)
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef) and node.name == function_name:
                        return (Path(filepath), node.lineno, source)
            except:
                continue

        return None

    def get_issue_report(self) -> Dict[str, Any]:
        """Generate comprehensive issue report"""
        analysis = self.analyze_codebase()

        critical_issues = [i for i in analysis.get("all_issues", []) if i.get("severity") == "CRITICAL"]
        warnings = [i for i in analysis.get("all_issues", []) if i.get("severity") == "WARNING"]

        return {
            "summary": {
                "files_analyzed": analysis["files_analyzed"],
                "total_issues": analysis["total_issues"],
                "critical": len(critical_issues),
                "warnings": len(warnings),
            },
            "issues_by_type": analysis["issues_by_type"],
            "critical_issues": critical_issues,
            "warnings": warnings,
        }
