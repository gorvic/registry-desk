"""SQLite schema."""

SCHEMA_SQL = r"""
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS registries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_filename TEXT NOT NULL,
    source_sha256 TEXT NOT NULL UNIQUE,
    page_count INTEGER NOT NULL,
    information_reference_number TEXT NOT NULL DEFAULT '',
    formed_at TEXT NOT NULL DEFAULT '',
    formed_by TEXT NOT NULL DEFAULT '',
    formation_basis TEXT NOT NULL DEFAULT '',
    query_type TEXT NOT NULL DEFAULT '',
    query_address TEXT NOT NULL DEFAULT '',
    imported_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS registry_pages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    registry_id INTEGER NOT NULL REFERENCES registries(id) ON DELETE CASCADE,
    page_number INTEGER NOT NULL,
    text TEXT NOT NULL,
    UNIQUE(registry_id, page_number)
);

CREATE TABLE IF NOT EXISTS properties (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    registry_id INTEGER NOT NULL REFERENCES registries(id) ON DELETE CASCADE,
    registry_number TEXT NOT NULL,
    object_description TEXT NOT NULL DEFAULT '',
    object_type_raw TEXT NOT NULL DEFAULT '',
    object_type TEXT NOT NULL DEFAULT '',
    edessb_identifier TEXT NOT NULL DEFAULT '',
    total_area TEXT NOT NULL,
    living_area TEXT,
    address_raw TEXT NOT NULL DEFAULT '',
    building_number TEXT NOT NULL DEFAULT '',
    unit_type TEXT NOT NULL DEFAULT '',
    unit_number TEXT NOT NULL DEFAULT '',
    source_page_start INTEGER NOT NULL,
    source_page_end INTEGER NOT NULL,
    raw_text TEXT NOT NULL,
    UNIQUE(registry_id, registry_number)
);

CREATE INDEX IF NOT EXISTS idx_properties_registry_unit
    ON properties(registry_id, unit_type, unit_number);

CREATE TABLE IF NOT EXISTS ownerships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    property_id INTEGER NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
    right_record_number TEXT NOT NULL DEFAULT '',
    right_type TEXT NOT NULL DEFAULT '',
    joint_ownership_type TEXT NOT NULL DEFAULT '',
    share_raw TEXT NOT NULL DEFAULT '',
    share_numerator INTEGER,
    share_denominator INTEGER,
    owner_name_raw TEXT NOT NULL,
    owner_name TEXT NOT NULL,
    owner_type TEXT NOT NULL DEFAULT '',
    legal_entity_code TEXT NOT NULL DEFAULT '',
    registration_country TEXT NOT NULL DEFAULT '',
    legacy_registration_raw TEXT NOT NULL DEFAULT '',
    legacy_registry_name TEXT NOT NULL DEFAULT '',
    legacy_record_number TEXT NOT NULL DEFAULT '',
    legacy_registered_at TEXT NOT NULL DEFAULT '',
    source_page INTEGER NOT NULL,
    raw_text TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_ownerships_property
    ON ownerships(property_id);
CREATE INDEX IF NOT EXISTS idx_ownerships_owner_name
    ON ownerships(owner_name COLLATE NOCASE);
"""
