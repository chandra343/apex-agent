"""Isolated In-Process / Subprocess Python REPL Execution."""
from __future__ import annotations

import io
import sys
import traceback
from typing import Any, Dict, Tuple


class PythonREPL:
    """Evaluates Python code with persistent session variables."""

    def __init__(self) -> None:
        self.locals_dict: Dict[str, Any] = {}
        self.globals_dict: Dict[str, Any] = {"__builtins__": __builtins__}

    def execute(self, code: str) -> Tuple[bool, str]:
        """Execute Python code and capture standard output/errors."""
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        redirected_stdout = io.StringIO()
        redirected_stderr = io.StringIO()

        sys.stdout = redirected_stdout
        sys.stderr = redirected_stderr

        try:
            # First try evaluating as an expression
            try:
                compiled = compile(code, "<apex-repl>", "eval")
                res = eval(compiled, self.globals_dict, self.locals_dict)
                sys.stdout = old_stdout
                sys.stderr = old_stderr
                out = redirected_stdout.getvalue()
                if res is not None:
                    out += f"\n=> {repr(res)}" if out else repr(res)
                return True, out.strip() or "[Executed successfully with no output]"
            except SyntaxError:
                # Fallback to exec for statements
                compiled = compile(code, "<apex-repl>", "exec")
                exec(compiled, self.globals_dict, self.locals_dict)
                sys.stdout = old_stdout
                sys.stderr = old_stderr
                out = redirected_stdout.getvalue()
                err = redirected_stderr.getvalue()
                res_str = (out + "\n" + err).strip()
                return True, res_str or "[Executed successfully with no output]"
        except Exception:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            tb = traceback.format_exc()
            return False, tb.strip()


# Global REPL instance
python_repl = PythonREPL()
