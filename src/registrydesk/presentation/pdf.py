"""PDF exporter for the clean owner view."""

from collections import defaultdict
from decimal import Decimal
import os
from pathlib import Path
from typing import Iterable

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import LongTable, Paragraph, SimpleDocTemplate, TableStyle
from xml.sax.saxutils import escape

from registrydesk.domain.errors import ErrorMessage, ExportError
from registrydesk.domain.exporting import EXPORT_FIELDS_BY_KEY, validate_export_fields
from registrydesk.domain.contracts import PropertyType
from registrydesk.domain.registry import RegistryDetails, RegistryRow
from registrydesk.presentation.values import fixed_two, pdf_export_value

_FONT_NAME = "RegistryDesk"
_FONT_BOLD_NAME = "RegistryDesk-Bold"


class _NumberedCanvas(canvas.Canvas):
    """Canvas that writes `Сторінка N із M` after the final page count is known."""

    def __init__(self, *args, font_name: str, **kwargs) -> None:
        self._saved_page_states: list[dict] = []
        self._footer_font_name = font_name
        super().__init__(*args, **kwargs)

    def showPage(self) -> None:  # noqa: N802
        """Cache the page state so the final page count can be drawn later."""
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self) -> None:
        """Replay cached pages with a stable ``page N of M`` footer."""
        page_count = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self._draw_page_number(page_count)
            super().showPage()
        super().save()

    def _draw_page_number(self, page_count: int) -> None:
        self.setFont(self._footer_font_name, 8)
        self.drawCentredString(
            self._pagesize[0] / 2,
            8 * mm,
            f"Сторінка {self._pageNumber} із {page_count}",
        )


def _font_candidates() -> tuple[tuple[Path, Path], ...]:
    """Return known Unicode-capable system font pairs in preference order."""
    windows = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts"
    return (
        (windows / "arial.ttf", windows / "arialbd.ttf"),
        (windows / "segoeui.ttf", windows / "segoeuib.ttf"),
        (
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        ),
        (
            Path("/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"),
            Path("/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf"),
        ),
    )


def _register_fonts() -> tuple[str, str]:
    """Register one Ukrainian-capable regular/bold pair once per process."""
    if _FONT_NAME in pdfmetrics.getRegisteredFontNames():
        return _FONT_NAME, _FONT_BOLD_NAME

    for regular, bold in _font_candidates():
        if regular.is_file():
            bold_path = bold if bold.is_file() else regular
            pdfmetrics.registerFont(TTFont(_FONT_NAME, regular))
            pdfmetrics.registerFont(TTFont(_FONT_BOLD_NAME, bold_path))
            return _FONT_NAME, _FONT_BOLD_NAME
    raise ExportError(ErrorMessage.PDF_FONT_NOT_FOUND)


def _column_weight(key: str) -> float:
    """Return relative PDF width based on the expected content density."""
    return {
        "unit_number": 0.9,
        "property_type": 1.2,
        "owner_no": 0.55,
        "owner_name": 4.8,
        "ownership_area": 1.35,
        "share": 0.9,
        "total_area": 1.3,
        "living_area": 1.3,
        "registry_number": 1.8,
        "right_record_numbers": 1.9,
        "right_type": 1.7,
        "joint_ownership_type": 1.8,
        "edessb_identifier": 2.8,
        "address": 4.5,
        "owner_type": 1.6,
        "legal_entity_code": 1.4,
        "registration_country": 1.5,
    }.get(key, 1.5)


class PdfExporter:
    """Create a printable grouped PDF with calculated numeric values."""

    def export(self, registry: RegistryDetails, field_keys: Iterable[str], path: Path) -> None:
        """Render a grouped, printable ownership table to PDF."""
        keys = validate_export_fields(field_keys)

        font_name, bold_font_name = _register_fonts()
        page_size = landscape(A4) if self._use_landscape(keys) else A4
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        document = SimpleDocTemplate(
            str(path),
            pagesize=page_size,
            leftMargin=10 * mm,
            rightMargin=10 * mm,
            topMargin=10 * mm,
            bottomMargin=15 * mm,
            title="RegistryDesk",
            author="RegistryDesk",
        )

        header_style = ParagraphStyle(
            "header",
            fontName=bold_font_name,
            fontSize=7.2,
            leading=8.2,
            alignment=TA_CENTER,
        )
        text_style = ParagraphStyle(
            "text",
            fontName=font_name,
            fontSize=7.0,
            leading=8.0,
            alignment=TA_LEFT,
        )
        center_style = ParagraphStyle(
            "center",
            parent=text_style,
            alignment=TA_CENTER,
        )
        number_style = ParagraphStyle(
            "number",
            parent=text_style,
            alignment=TA_RIGHT,
        )
        section_style = ParagraphStyle(
            "section",
            fontName=bold_font_name,
            fontSize=7.2,
            leading=8.2,
            alignment=TA_CENTER,
        )
        total_label_style = ParagraphStyle(
            "total-label",
            fontName=bold_font_name,
            fontSize=7.0,
            leading=8.0,
            alignment=TA_LEFT,
        )
        total_number_style = ParagraphStyle(
            "total-number",
            fontName=bold_font_name,
            fontSize=7.0,
            leading=8.0,
            alignment=TA_RIGHT,
        )

        data: list[list[Paragraph]] = [
            [
                Paragraph(escape(EXPORT_FIELDS_BY_KEY[key].header_label), header_style)
                for key in keys
            ]
        ]
        commands: list[tuple] = []
        row_index = 1
        sequence = 1

        for section_type, section_title in (
            (PropertyType.APARTMENT.value, "КВАРТИРИ"),
            (PropertyType.PREMISES.value, "НЕЖИТЛОВІ ПРИМІЩЕННЯ"),
        ):
            section_rows = [row for row in registry.rows if row.property_type == section_type]
            if not section_rows:
                continue

            data.append(
                [Paragraph(section_title, section_style)]
                + [Paragraph("", section_style) for _ in keys[1:]]
            )
            commands.extend(
                [
                    ("SPAN", (0, row_index), (len(keys) - 1, row_index)),
                    (
                        "BACKGROUND",
                        (0, row_index),
                        (len(keys) - 1, row_index),
                        colors.HexColor("#E5E5E5"),
                    ),
                ]
            )
            row_index += 1

            by_property: dict[int, list[RegistryRow]] = defaultdict(list)
            property_order: list[int] = []
            for row in section_rows:
                if row.property_id not in by_property:
                    property_order.append(row.property_id)
                by_property[row.property_id].append(row)

            for property_id in property_order:
                owner_rows = by_property[property_id]
                first_table_row = row_index
                last_table_row = row_index + len(owner_rows) - 1

                for clean_row in owner_rows:
                    values: list[Paragraph] = []
                    for key in keys:
                        value = pdf_export_value(key, clean_row, sequence)
                        style = self._style_for(key, text_style, center_style, number_style)
                        values.append(Paragraph(escape(value), style))
                    data.append(values)
                    row_index += 1
                    sequence += 1

                if len(owner_rows) > 1:
                    # Property-level values belong to the property, not each
                    # owner.  Spanning keeps that relationship visible in print.
                    for column, key in enumerate(keys):
                        if EXPORT_FIELDS_BY_KEY[key].property_level:
                            commands.append(
                                ("SPAN", (column, first_table_row), (column, last_table_row))
                            )

        if "total_area" in keys:
            total_col = keys.index("total_area")
            total_area = sum(
                (row.total_area for row in self._first_row_per_property(registry.rows)),
                start=Decimal("0"),
            )
            total_values = [Paragraph("", text_style) for _ in keys]
            total_values[0] = Paragraph("Усього", total_label_style)
            total_values[total_col] = Paragraph(fixed_two(total_area), total_number_style)
            data.append(total_values)

        available_width = page_size[0] - document.leftMargin - document.rightMargin
        weights = [_column_weight(key) for key in keys]
        weight_sum = sum(weights)
        widths = [available_width * weight / weight_sum for weight in weights]

        table = LongTable(
            data,
            colWidths=widths,
            repeatRows=1,
            hAlign="LEFT",
            splitByRow=1,
        )
        base_style = [
            ("GRID", (0, 0), (-1, -1), 0.55, colors.black),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F2F2F2")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 2.0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 2.0),
            ("TOPPADDING", (0, 0), (-1, -1), 1.3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 1.3),
        ]
        table.setStyle(TableStyle(base_style + commands))

        document.build(
            [table],
            canvasmaker=lambda *args, **kwargs: _NumberedCanvas(
                *args, font_name=font_name, **kwargs
            ),
        )

    @staticmethod
    def _use_landscape(keys: tuple[str, ...]) -> bool:
        """Switch to landscape when selected columns would be too dense on A4."""
        return len(keys) > 7 or sum(_column_weight(key) for key in keys) > 11.0

    @staticmethod
    def _style_for(
        key: str,
        text_style: ParagraphStyle,
        center_style: ParagraphStyle,
        number_style: ParagraphStyle,
    ) -> ParagraphStyle:
        if key in {"owner_name", "address", "right_record_numbers", "edessb_identifier"}:
            return text_style
        if key in {"total_area", "living_area", "ownership_area", "share"}:
            return number_style
        return center_style

    @staticmethod
    def _first_row_per_property(rows: tuple[RegistryRow, ...]) -> tuple[RegistryRow, ...]:
        seen: set[int] = set()
        result: list[RegistryRow] = []
        for row in rows:
            if row.property_id not in seen:
                seen.add(row.property_id)
                result.append(row)
        return tuple(result)
