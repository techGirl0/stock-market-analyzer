"""Generate the SAD 5.2 class diagram from code (SCRUM-91).

Steps (all automatic, no manual drawing):
  1. Run pyreverse (part of pylint) on the FastAPI backend modules of the
     Watchlist CRUD and authentication use cases -> raw PlantUML files.
  2. Group the generated classes into coloured Model / View / Controller
     regions, based on the package each class lives in.
  3. FastAPI routers are plain functions, so pyreverse has no class to draw for
     the Controller layer. The router endpoints (HTTP method, path, handler) and
     their dependencies are read from the controller source code with ``ast``
     and added as <<APIRouter>> boxes.
  4. Optionally render PNG/SVG with PlantUML (``--plantuml path/to/plantuml.jar``).

Run from the repository root:
    python documentation/architecture/generate_class_diagram.py --plantuml plantuml.jar
"""

from __future__ import annotations

import argparse
import ast
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
OUT = Path(__file__).resolve().parent
GENERATED = OUT / "generated"
PROJECT = "WolfStreetSignal"

MODULES = [
    "app.models.base",
    "app.models.user",
    "app.models.refresh_token",
    "app.models.watchlist",
    "app.schemas.watchlists",
    "app.schemas.auth",
    "app.services.watchlists",
    "app.services.auth",
    "app.services.instruments",
    "app.connectors.market",
    "app.controllers.watchlists",
    "app.controllers.auth",
]

# Module prefix -> (region title, colour). Order matters: first match wins.
REGIONS = [
    ("app.controllers.", "CONTROLLER - FastAPI routers (app/controllers)", "#FFE0B2"),
    ("app.schemas.", "VIEW - Pydantic schemas = API contract rendered by Next.js (app/schemas)", "#BBDEFB"),
    ("app.models.", "MODEL - SQLAlchemy entities (app/models)", "#C8E6C9"),
    ("app.services.", "MODEL - business services using FastCRUD (app/services)", "#DCEDC8"),
    ("app.connectors.", "MODEL - market data adapters (app/connectors)", "#F0F4C3"),
]

HTTP_METHODS = {"get", "post", "put", "patch", "delete"}


def region_of(module: str) -> tuple[str, str]:
    for prefix, title, colour in REGIONS:
        if module.startswith(prefix):
            return title, colour
    raise ValueError(f"No MVC region for {module}")


def run_pyreverse() -> None:
    exe = shutil.which("pyreverse")
    cmd = [exe] if exe else [sys.executable, "-m", "pylint.pyreverse.main"]
    GENERATED.mkdir(exist_ok=True)
    cmd += [
        "-o", "puml",
        "-p", PROJECT,
        "-d", str(GENERATED),
        "--module-names=y",
        "--filter-mode=PUB_ONLY",
        *MODULES,
    ]
    print("Running:", " ".join(Path(c).name if i == 0 else c for i, c in enumerate(cmd)))
    subprocess.run(cmd, cwd=BACKEND, check=True)


def parse_classes(puml: str) -> tuple[dict[str, list[str]], list[str]]:
    """Return {alias: class block lines} and the relation lines from pyreverse."""
    blocks: dict[str, list[str]] = {}
    relations: list[str] = []
    lines = puml.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        match = re.match(r'class "(.+?)" as (\S+) \{', line)
        if match:
            alias = match.group(2)
            short = alias.rsplit(".", 1)[1]
            # strip pyreverse colouring of exception classes, show short names
            header = f'class "{short}" as {alias} {{'
            body = []
            i += 1
            while lines[i] != "}":
                body.append(lines[i])
                i += 1
            blocks[alias] = [header, *body, "}"]
        elif re.match(r"\S+ (--\|>|--o|--\*|-->|\.\.>|\.\.\|>) \S+", line):
            relations.append(line)
        i += 1
    return blocks, relations


def controller_routers(known: set[str]) -> tuple[dict[str, list[str]], list[str]]:
    """Read each controller module and describe its APIRouter endpoints."""
    blocks: dict[str, list[str]] = {}
    relations: list[str] = []
    for module in (m for m in MODULES if m.startswith("app.controllers.")):
        path = BACKEND / (module.replace(".", "/") + ".py")
        tree = ast.parse(path.read_text(encoding="utf-8"))
        prefix = ""
        endpoints: list[str] = []
        imported: list[str] = []
        for node in tree.body:
            if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("app."):
                imported += [f"{node.module}.{a.name}" for a in node.names]
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
                for kw in node.value.keywords:
                    if kw.arg == "prefix" and isinstance(kw.value, ast.Constant):
                        prefix = kw.value.value
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for dec in node.decorator_list:
                    if (
                        isinstance(dec, ast.Call)
                        and isinstance(dec.func, ast.Attribute)
                        and dec.func.attr in HTTP_METHODS
                    ):
                        route = dec.args[0].value if dec.args else ""
                        endpoints.append(f"  +{dec.func.attr.upper()} {prefix}{route} : {node.name}()")
        alias = f"{module}.router"
        name = module.rsplit(".", 1)[1]
        blocks[alias] = [f'class "{name} router" as {alias} <<APIRouter>> {{', *endpoints, "}"]
        for target in imported:
            if target in known:
                kind = "calls" if ".services." in target else "returns / validates"
                relations.append(f"{alias} ..> {target} : {kind}")
    return blocks, relations


def build_class_diagram(blocks: dict[str, list[str]], relations: list[str]) -> str:
    grouped: dict[tuple[str, str], dict[str, list[str]]] = {}
    for alias, block in blocks.items():
        module = alias.rsplit(".", 1)[0]
        grouped.setdefault(region_of(module), {}).setdefault(module, []).extend(block)

    out = [
        "@startuml class-diagram-mvc",
        "' GENERATED FILE - do not edit by hand.",
        "' Source: pyreverse output + documentation/architecture/generate_class_diagram.py",
        "set namespaceSeparator none",
        "skinparam packageStyle rectangle",
        "skinparam classBackgroundColor #FFFFFF",
        "skinparam shadowing false",
        "skinparam defaultFontSize 12",
        "hide empty members",
        f"title {PROJECT} backend - class diagram (Watchlist CRUD + Auth) with MVC regions",
    ]
    order = [r[1] for r in REGIONS]
    for (title, colour) in sorted(grouped, key=lambda r: order.index(r[0])):
        out.append(f'package "{title}" {colour} {{')
        for module, block in sorted(grouped[(title, colour)].items()):
            out.append(f'  package "{module}" {{')
            out += [f"    {line}" for line in block]
            out.append("  }")
        out.append("}")
    out += relations
    out += [
        "legend right",
        "  |= Colour |= MVC role |",
        "  |<#FFE0B2>| Controller: FastAPI routers |",
        "  |<#BBDEFB>| View: Pydantic schemas (API contract) -> Next.js UI |",
        "  |<#C8E6C9>| Model: SQLAlchemy entities |",
        "  |<#DCEDC8>| Model: services (business logic, FastCRUD) |",
        "  |<#F0F4C3>| Model: external market-data adapters |",
        "endlegend",
        "@enduml",
    ]
    return "\n".join(out) + "\n"


def build_package_diagram(puml: str) -> str:
    lines = []
    for line in puml.splitlines():
        match = re.match(r'package "(\S+)" as (\S+) \{', line)
        if match:
            title, colour = region_of(match.group(1) + ".")
            role = title.split(" - ")[0]
            line = f'package "{match.group(1)}\\n<<{role}>>" as {match.group(2)} {colour} {{'
        elif line.startswith("@startuml"):
            line = "@startuml package-diagram-mvc\n' GENERATED FILE - pyreverse package diagram coloured by MVC role"
            line += "\nskinparam shadowing false\nleft to right direction"
        lines.append(line)
    return "\n".join(lines) + "\n"


def render(plantuml_jar: Path, files: list[Path]) -> None:
    for fmt in ("png", "svg"):
        subprocess.run(
            ["java", "-jar", str(plantuml_jar), f"-t{fmt}", "-o", str(OUT), *map(str, files)],
            check=True,
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plantuml", type=Path, help="path to plantuml.jar to render PNG/SVG")
    args = parser.parse_args()

    run_pyreverse()
    classes_raw = (GENERATED / f"classes_{PROJECT}.puml").read_text(encoding="utf-8")
    packages_raw = (GENERATED / f"packages_{PROJECT}.puml").read_text(encoding="utf-8")

    blocks, relations = parse_classes(classes_raw)
    router_blocks, router_relations = controller_routers(set(blocks))
    blocks.update(router_blocks)

    class_file = OUT / "class-diagram-mvc.puml"
    package_file = OUT / "package-diagram-mvc.puml"
    class_file.write_text(build_class_diagram(blocks, relations + router_relations), encoding="utf-8")
    package_file.write_text(build_package_diagram(packages_raw), encoding="utf-8")
    print("Wrote", class_file.relative_to(ROOT), "and", package_file.relative_to(ROOT))

    if args.plantuml:
        render(args.plantuml, [class_file, package_file])
        print("Rendered PNG and SVG into", OUT.relative_to(ROOT))


if __name__ == "__main__":
    main()
