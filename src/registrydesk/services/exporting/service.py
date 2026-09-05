"""Export orchestration with heavy renderers loaded only when requested."""

from pathlib import Path

from registrydesk.domain.errors import ErrorMessage, ExportError
from registrydesk.domain.exporting import ExportFormat, validate_export_fields
from registrydesk.domain.registry import RegistryDetails


class ExportService:
    """Dispatch exports without loading optional renderer stacks at startup."""

    def export(
        self,
        registry: RegistryDetails,
        export_format: ExportFormat,
        field_keys: tuple[str, ...],
        path: Path,
    ) -> None:
        """Validate the selection and invoke the concrete renderer on demand."""
        field_keys = validate_export_fields(field_keys)

        # These local imports are intentional: browsing/importing registries must
        # not pay the OpenPyXL/ReportLab startup cost when no export is requested.
        if export_format is ExportFormat.XLSX:
            from registrydesk.presentation.xlsx import XlsxExporter

            XlsxExporter().export(registry, field_keys, path)
            return
        if export_format is ExportFormat.PDF:
            from registrydesk.presentation.pdf import PdfExporter

            PdfExporter().export(registry, field_keys, path)
            return
        if export_format is ExportFormat.CSV:
            from registrydesk.presentation.csv import CsvExporter

            CsvExporter().export(registry, field_keys, path)
            return
        raise ExportError(ErrorMessage.EXPORT_FORMAT_UNSUPPORTED.format(value=export_format))
