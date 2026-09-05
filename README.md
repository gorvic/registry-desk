# RegistryDesk

**RegistryDesk** — невеликий локальний desktop-застосунок для імпорту PDF-довідок ЦНАП із Державного реєстру речових прав на нерухоме майно та перетворення їх на чистий структурований реєстр співвласників.

> Поточна версія: **0.5.0**

Застосунок орієнтований на один практичний сценарій: імпортувати офіційний PDF по багатоквартирному будинку, переглянути нормалізовані записи власників, знайти потрібний об’єкт і сформувати XLSX, PDF або CSV для подальшої роботи.

## Основні можливості

- імпорт PDF-довідок ЦНАП щодо багатоквартирного будинку;
- локальне зберігання розібраних даних у SQLite;
- read-only список імпортованих реєстрів;
- нормалізована таблиця співвласників із точними частками;
- пошук по всіх видимих колонках;
- природне сортування номерів квартир і приміщень;
- експорт вибраних колонок у **XLSX**, **PDF** або **CSV**;
- startup theme через `.env`: `system`, `light` або `dark`;
- усі важкі optional бібліотеки експорту/парсингу завантажуються лише під час реальної операції.

RegistryDesk не редагує імпортований документ. Якщо довідку потрібно обробити повторно, її snapshot видаляється цілком і PDF імпортується заново.

## Основний сценарій

1. На сторінці **«Імпортовані реєстри»** натиснути **«Додати»**.
2. Вибрати PDF-довідку ЦНАП.
3. RegistryDesk розбере документ, перевірить частки та збереже snapshot у локальній БД.
4. Відкрити реєстр і використовувати пошук/сортування.
5. Натиснути **«Експорт»**, вибрати формат, поля та їх порядок.

## Експорт

### XLSX

XLSX створює робочу таблицю з окремими секціями квартир і приміщень. Поля рівня об’єкта об’єднуються для кількох співвласників, частки та площа у власності записуються як Excel-формули, а числові поля мають формат `0.00`.

### PDF

PDF формує готову до перегляду/друку таблицю. Частки виводяться точними дробами (`1`, `1/3`, `11/20`), площі — з двома знаками після коми, сторінки нумеруються автоматично.

### CSV

CSV — плоске представлення з одним рядком на один чистий ownership record. Файл записується у UTF-8 BOM із роздільником `;`, а дробові значення переводяться у компактне десяткове представлення без використання `float` для внутрішніх розрахунків.

## Дані

Усі робочі дані залишаються локально. SQLite-база створюється у:

```text
.data/registrydesk.db
```

У БД зберігаються:

- метадані довідки;
- повний видобутий текст сторінок;
- об’єкти нерухомості;
- площі й адреси;
- записи про права власності;
- точні частки;
- власники та дані юридичних осіб;
- доступні відомості про попередню реєстрацію.

Оригінальний PDF у SQLite не копіюється.

## Точність часток

Частки моделюються через `Fraction`, площі — через `Decimal`. Наприклад, `1/3`, `2/3`, `11/20` не перетворюються на `float` і не втрачають точність у domain/storage workflow.

Якщо в одному об’єкті один власник має кілька записів про право, clean view агрегує ці записи. Наприклад, два права по `1/2` для одного власника стають однією часткою `1`.

## Тема

Тема вибирається тільки при запуску програми через `.env` у корені застосунку:

```env
THEME=system
```

Підтримуються рівно три значення:

```text
system
light
dark
```

Значення за замовчуванням — `system`. Runtime-перемикання теми навмисно відсутнє.

Для локального налаштування скопіюйте `.env.example` у `.env`.

## Встановлення для розробки

Потрібен Python 3.11+.

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
python main.py
```

Або:

```text
run.cmd
```

## Залежності

- **PySide6** — desktop GUI;
- **PyMuPDF** — PDF parser;
- **openpyxl** — XLSX renderer;
- **ReportLab** — PDF renderer;
- **python-dotenv** — startup `.env` settings;
- **sqlite3** — локальне сховище зі стандартної бібліотеки Python.

PyMuPDF, openpyxl і ReportLab не входять у normal bootstrap import path. Вони імпортуються лише при першому імпорті PDF або відповідному експорті.

## Архітектура

```text
interfaces → application → services → repositories → storage
                     ↘ presentation (через export service)
```

Фізична структура:

```text
src/registrydesk/
├── application/     # тонкий GUI-facing facade
├── common/          # dependency-free sorting/helpers
├── config/          # runtime paths, .env settings, Theme contract
├── domain/          # immutable data, errors, export/property contracts
├── interfaces/      # Qt launcher та GUI
│   └── gui/
│       ├── controllers/
│       ├── dialogs/
│       ├── models/
│       ├── pages/
│       ├── contracts.py
│       └── geometry.py
├── presentation/    # XLSX/PDF/CSV renderers
├── repositories/    # SQLite repository
├── services/        # registry workflows, importer/export orchestration
├── storage/         # sqlite3 gateway, schema, migrations
├── bootstrap.py     # explicit dependency assembly
└── runtime.py       # thin script entry point
```

GUI не імпортує services/repositories/storage/presentation напряму. Application не знає про SQLite або конкретні renderers. SQLite залишається навмисно простим `sqlite3` backend: RegistryDesk — локальний parser/converter, тому SQLAlchemy тут не додає практичної цінності.

Докладніше див. `ARCHITECTURE.md`.

## Тести

```powershell
pytest
```

Тести покривають parser, repository aggregation, sorting, XLSX/PDF/CSV output, `.env` theme settings, startup dependency graph і структурні architecture guards.

## Поточні межі

Parser орієнтований на структуру PDF-довідок ЦНАП, яку підтримує поточна версія. Якщо формат державної довідки зміниться, parser потрібно адаптувати до нової структури документа.
