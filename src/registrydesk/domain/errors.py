"""Application-facing error taxonomy and centralized messages."""

from enum import StrEnum


class ErrorMessage(StrEnum):
    """User-facing messages for expected application/export failures."""

    REGISTRY_NOT_FOUND = "Реєстр не знайдено."
    DUPLICATE_REGISTRY = "Цю PDF-довідку вже імпортовано."
    EXPORT_FIELDS_REQUIRED = "Потрібно вибрати хоча б одне поле для експорту."
    EXPORT_FIELDS_UNKNOWN = "Невідомі поля експорту: {items}"
    EXPORT_FORMAT_UNSUPPORTED = "Непідтримуваний формат експорту: {value}"
    PDF_FONT_NOT_FOUND = (
        "Не знайдено системний шрифт із підтримкою української мови для експорту PDF."
    )


class RegistryImportMessage(StrEnum):
    """Parser-specific messages kept independent from PyMuPDF exceptions."""

    DECIMAL_PARSE = "Не вдалося розібрати {field}: {value!r}"
    INVALID_SHARE = "Некоректна частка власності: {value!r}"
    OWNER_MISSING = "Не знайдено власника для запису про право {number} (сторінка {page})."
    REGISTRY_NUMBER_MISSING = "Не знайдено реєстраційний номер об’єкта (сторінка {page})."
    TOTAL_AREA_MISSING = "Не знайдено загальну площу об’єкта {number} (сторінка {page})."
    ADDRESS_MISSING = "Не знайдено адресу об’єкта {number}."
    OWNERSHIP_BLOCK_MISSING = "Не знайдено блок прав власності для об’єкта {number}."
    OWNERS_MISSING = "Не знайдено власників об’єкта {number}."
    PDF_OPEN_FAILED = "Не вдалося відкрити PDF: {error}"
    UNSUPPORTED_DOCUMENT = "PDF не містить підтримуваного блоку Державного реєстру речових прав."
    PROPERTIES_MISSING = "Не вдалося видобути жодного об’єкта нерухомості."
    DUPLICATE_PROPERTY = "Дубльований реєстраційний номер об’єкта: {number}"
    SHARES_MISSING = "Для об’єкта {number} є кілька власників, але не для всіх указана частка."
    SHARES_SUM_INVALID = "Сума часток об’єкта {number} дорівнює {value}, а не 1."


class RegistryDeskError(Exception):
    """Base class for expected RegistryDesk operation failures."""


class ValidationError(RegistryDeskError):
    """Invalid user/application input that can be reported without a traceback."""



class NotFoundError(RegistryDeskError):
    """Requested persisted domain object does not exist."""



class DuplicateRegistryError(RegistryDeskError):
    """The exact source PDF has already been imported."""



class RegistryImportError(RegistryDeskError):
    """Supported registry parsing or validation failed."""



class ExportError(RegistryDeskError):
    """Export configuration or rendering failed in an expected way."""

