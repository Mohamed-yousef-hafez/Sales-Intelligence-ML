"""Checks a generated Power BI project against Microsoft's published JSON schemas.

    python tools/validate_pbip.py <project folder> [schema folder]

The schemas come from https://github.com/microsoft/json-schemas . If the schema folder does not exist,
it is downloaded with git (needs git and internet; about 4 MB). Needs:  pip install jsonschema referencing
"""
import json
from pathlib import Path
import subprocess
import sys

from jsonschema import Draft7Validator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT7

PREFIX = "https://developer.microsoft.com/json-schemas/fabric/"


def get_schemas(folder):
    folder = Path(folder)
    if not (folder / "fabric").exists():
        subprocess.run(["git", "clone", "-q", "--depth", "1", "--filter=blob:none", "--sparse",
                        "https://github.com/microsoft/json-schemas.git", str(folder)], check=True)
        subprocess.run(["git", "-C", str(folder), "sparse-checkout", "set", "fabric"], check=True)
    return folder


def validate_project(project, schema_folder="/tmp/json-schemas"):
    """Returns a list of problems (empty list = every JSON file follows its schema)."""
    schema_root = get_schemas(schema_folder) / "fabric"

    def retrieve(uri):
        if not uri.startswith(PREFIX):
            raise KeyError(uri)
        return Resource.from_contents(json.loads((schema_root / uri[len(PREFIX):]).read_text(encoding="utf-8")), default_specification=DRAFT7)

    registry = Registry(retrieve=retrieve)
    problems, checked = [], 0
    for path in sorted(Path(project).rglob("*")):
        if not path.is_file() or (path.suffix not in (".json", ".pbip", ".pbir", ".pbism") and path.name != ".platform"):
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        url = data.get("$schema", "")
        if not url.startswith(PREFIX):
            problems.append(f"{path}: no Microsoft $schema")
            continue
        schema = json.loads((schema_root / url[len(PREFIX):]).read_text(encoding="utf-8"))
        for error in Draft7Validator(schema, registry=registry).iter_errors(data):
            problems.append(f"{path.relative_to(project)}: {'/'.join(map(str, error.absolute_path))}: {error.message[:160]}")
        checked += 1
    return problems, checked


if __name__ == "__main__":
    folder = sys.argv[1]
    issues, count = validate_project(folder, *(sys.argv[2:3] or []))
    print(f"{count} JSON files checked, {len(issues)} problems")
    for issue in issues[:40]:
        print("  ", issue)
    sys.exit(1 if issues else 0)
