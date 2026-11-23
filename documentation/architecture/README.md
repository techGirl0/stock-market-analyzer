# Architecture artifacts (SAD sections 2 and 5.2)

The section text itself is in the
[Software Architecture Document](../SoftwareArchitectureDocument.md).
This folder holds the diagram sources and the script that generates them.

| File | What it is |
|------|------------|
| `generate_class_diagram.py` | Script that regenerates every diagram in this folder from the code |
| `generated/classes_WolfStreetSignal.puml` | Raw pyreverse class diagram (unchanged tool output) |
| `generated/packages_WolfStreetSignal.puml` | Raw pyreverse package diagram (unchanged tool output) |
| `class-diagram-mvc.puml` | SAD 5.2 class diagram source (PlantUML) |
| `class-diagram-mvc.png` → `../Media/class-diagram-mvc.png` | SAD 5.2 class diagram with Model / View / Controller regions |
| `package-diagram-mvc.puml` | Module dependency diagram source (PlantUML) |
| `package-diagram-mvc.png` → `../Media/package-diagram-mvc.png` | Module dependency diagram coloured by MVC role |

## How the class diagram is generated (no manual drawing)

1. **pyreverse** (from pylint) reads the FastAPI backend modules of the
   Watchlist CRUD and Authentication use cases and writes PlantUML files to
   `generated/`.
2. `generate_class_diagram.py` puts each generated class into a coloured MVC
   region based on its package:

   | Package | MVC role | Colour |
   |---------|----------|--------|
   | `app/controllers` (FastAPI routers) | Controller | orange |
   | `app/schemas` (Pydantic request/response models) | View (API contract shown by Next.js) | blue |
   | `app/models` (SQLAlchemy entities) | Model | green |
   | `app/services` (business logic with FastCRUD) | Model | light green |
   | `app/connectors` (market-data adapters) | Model | yellow-green |

3. FastAPI routers are plain functions, so pyreverse has no class to draw for
   the Controller layer. The script reads the controller source with Python's
   `ast` module and adds one `<<APIRouter>>` box per router. Each box lists its
   endpoints (HTTP method, path and handler) and has a dependency on every
   schema and service class the router imports.
4. PlantUML renders the `.puml` files to PNG and SVG.

## Re-run it

Tool versions used: **pylint/pyreverse 4.1.4, astroid 4.3.4, Python 3.11.4,
PlantUML 1.2024.8, Java 21**.

From the repository root:

```powershell
py -m pip install "pylint==4.1.4"
py documentation/architecture/generate_class_diagram.py --plantuml C:\path\to\plantuml.jar
```

pyreverse does not import the code; it parses it statically. You don't need
the backend dependencies installed to run it.

Without `--plantuml` the script writes only the `.puml` files. You can render
them in either of these ways:

- **IntelliJ / PyCharm:** install the *PlantUML Integration* plugin, open the
  `.puml` file and use *Save diagram* in the preview.
- **Command line:**
  `java -jar plantuml.jar -tpng documentation/architecture/*.puml`.
  Class diagrams need Graphviz (`winget install Graphviz.Graphviz`). Without
  Graphviz, add `-Playout=smetana` to use PlantUML's built-in layout engine.

## Scope and known limits

- The diagram covers the code that exists for the first use case (Watchlist
  CRUD) and the login it depends on. It also includes
  `services/instruments.py` and `connectors/market.py`, because the watchlist
  service checks tickers through them. Other modules (`alerts`, `portfolio`,
  `research`, `analysis`) are left out to keep the diagram readable; to include
  them, add them to `MODULES` in the script.
- pyreverse does not draw SQLAlchemy `relationship()` links as associations.
  They appear as typed attributes instead (for example
  `User.watchlists : Mapped[list['Watchlist']]`). `package-diagram-mvc.png`
  shows the module dependencies, and the EER model (SAD section 9) shows the
  table relations.
- `ai_module/` (the Streamlit prototype) is mostly functions, not classes, so
  pyreverse gives a nearly empty diagram for it. It is covered in the SAD
  section 2 text instead.
