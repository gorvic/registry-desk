"""Centralized stable GUI geometry values."""

from registrydesk.interfaces.gui.contracts import RegistryListColumn, RegistryTableColumn

MAIN_WINDOW_SIZE = (1000, 760)
MAIN_WINDOW_MINIMUM_SIZE = (1000, 650)
EXPORT_DIALOG_SIZE = (720, 500)
EXPORT_MOVE_BUTTON_WIDTH = 48

REGISTRY_LIST_COLUMN_WIDTHS = {
    RegistryListColumn.FORMED_AT: 150,
    RegistryListColumn.REFERENCE_NUMBER: 120,
    RegistryListColumn.ADDRESS: 430,
    RegistryListColumn.PROPERTY_COUNT: 90,
    RegistryListColumn.OWNER_COUNT: 90,
}

REGISTRY_TABLE_COLUMN_WIDTHS = {
    RegistryTableColumn.UNIT: 120,
    RegistryTableColumn.OWNER: 320,
    RegistryTableColumn.TOTAL_AREA: 120,
    RegistryTableColumn.SHARE: 90,
    RegistryTableColumn.OWNERSHIP_AREA: 140,
    RegistryTableColumn.REGISTRY_NUMBER: 180,
    RegistryTableColumn.RIGHT_RECORD_NUMBERS: 190,
}
