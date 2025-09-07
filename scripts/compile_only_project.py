# small helper to compile all .py under repo excluding large dirs
import os
import py_compile
import sys

root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
exclude_dirs = {"node_modules", "frontend", "venv", ".venv", ".git", "__pycache__"}
errors = []
for dirpath, dirnames, filenames in os.walk(root):
    # filter out excluded dirs in-place to speed walk
    dirnames[:] = [d for d in dirnames if d not in exclude_dirs]
    for f in filenames:
        if not f.endswith(".py"):
            continue
        path = os.path.join(dirpath, f)
        try:
            py_compile.compile(path, doraise=True)
        except Exception as e:
            errors.append((path, repr(e)))

if not errors:
    print("OK: no syntax errors detected in scanned files")
    sys.exit(0)

print("FOUND ERRORS:")
for p, e in errors:
    print(f"--- {p} ---")
    print(e)

sys.exit(2)
