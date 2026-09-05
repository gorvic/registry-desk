# RegistryDesk architecture baseline — 0.5.0

RegistryDesk is intentionally a small local desktop parser/converter. The architecture follows the same responsibility rules as the larger OSBB application, but does not reproduce abstractions that have no practical value at this scale.

## Dependency direction

```text
interfaces
    ↓
application
    ↓
services
    ↓
repositories
    ↓
storage
```

Presentation renderers are invoked by the export service and do not leak into application or GUI contracts.

### `domain`

Owns immutable registry data, export/property contracts and expected operation errors. It has no GUI, database or presentation dependencies.

### `common`

Contains small dependency-free helpers such as Ukrainian/natural sorting. Business metadata such as property-type order belongs to domain contracts rather than parallel dictionaries.

### `storage`

Owns the local SQLite connection, schema and forward migrations. RegistryDesk intentionally uses the standard-library `sqlite3` module. SQLAlchemy is not used because this application has no requirement for interchangeable remote database backends.

### `repositories`

Owns SQL and maps source-level database rows into normalized domain read models. The repository aggregates multiple rights belonging to the same owner/property and returns a clean `RegistryDetails` view.

### `services`

Owns registry workflows. `RegistryService` coordinates import, reads, delete and export. The PDF parser is imported only when a PDF is actually imported. `ExportService` validates the requested field set and loads the selected renderer only when export is requested.

### `application`

A thin GUI-facing facade over `RegistryService`. It does not import repositories, storage or presentation modules.

### `interfaces`

Owns Qt. `MainWindow` is only the shell/composition point for pages and signal wiring. `RegistryController` owns GUI workflows such as file selection, import, delete, open and export. GUI code talks to `RegistryApplication`, not lower layers.

## GUI contracts and geometry

Column identity/labels are typed in `interfaces/gui/contracts.py`. Stable sizes and widths are centralized in `interfaces/gui/geometry.py`.

Geometry does not contain Qt behavior. Pages remain responsible for applying their widths/sizes.

## Theme

`THEME` is read once at application startup from `.env` via `AppSettings`.

Allowed values:

```text
system
light
dark
```

Default is `system`. The system theme applies only the palette-aware base stylesheet. Explicit light/dark modes add a small dedicated stylesheet. Runtime theme switching is intentionally not part of the application.

## Startup and heavy dependencies

Normal bootstrap does not import PyMuPDF, openpyxl or ReportLab.

```text
PDF import   → services.importing.pdf_importer → PyMuPDF
XLSX export  → presentation.xlsx              → openpyxl
PDF export   → presentation.pdf               → ReportLab
CSV export   → presentation.csv               → stdlib csv
```

Imports are ordinary local imports, so bundlers can discover the modules statically while source-run startup remains lightweight.

## Data model

Imported documents are immutable snapshots. SQLite stores source-level metadata, extracted pages, properties and ownership records. The repository derives the clean owner view on read.

`Decimal` is used for areas and `Fraction` for ownership shares. Derived ownership area is a domain property rather than duplicated persisted state.

## Error boundaries

Expected operation failures use a small semantic error taxonomy. GUI controllers are allowed to catch broad exceptions at the Qt event boundary so errors do not escape the event loop; lower layers should not use broad catches except when translating a third-party boundary failure such as opening a PDF.

## Source documentation conventions

RegistryDesk is intended to be readable as public source code. Production modules and public classes/methods document their responsibility or contract with docstrings. Inline comments are reserved for reasoning that is not obvious from the code itself: parser quirks, data invariants, transaction boundaries, exact-share handling, GUI event boundaries, and intentional deferred imports.

The project deliberately avoids comments that merely restate Python syntax. This keeps documentation useful rather than noisy.
