import ast
from pathlib import Path


def test_app_has_no_expression_that_streamlit_would_print():
    """Streamlit prints the value of a bare expression such as `st.success(x) if ok else st.warning(x)`
    (it showed pages of DeltaGenerator documentation). Only calls and docstrings are allowed as statements."""
    source = (Path(__file__).parent.parent / "app.py").read_text(encoding="utf-8")
    bad = [
        (node.lineno, type(node.value).__name__)
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Expr) and not isinstance(node.value, (ast.Call, ast.Constant, ast.Await))
    ]
    assert bad == []
