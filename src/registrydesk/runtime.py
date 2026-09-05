"""Console/script entry point kept intentionally thin."""


def run() -> int:
    """Import Qt only when the executable/script actually starts the GUI."""
    from registrydesk.interfaces.launcher import run as launch

    return launch()
