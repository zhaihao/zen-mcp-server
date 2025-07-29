import logging

from rich.logging import RichHandler

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True, tracebacks_show_locals=True)]
)

slog = logging.getLogger("slog")
slog.setLevel(logging.DEBUG)