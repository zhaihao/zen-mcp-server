import importlib.util
import sys
from pathlib import Path

from fastapi import FastAPI

app = FastAPI()

router_dirs = [
    Path(__file__).parent / "endpoint",
]

for routers_dir in router_dirs:
    if not routers_dir.exists():
        continue
    for router_file in routers_dir.glob("*.py"):
        if router_file.name.startswith("_") or router_file.name.startswith("test"):
            continue
        module_name = f"{routers_dir.name}_{router_file.stem}"
        spec = importlib.util.spec_from_file_location(module_name, str(router_file))
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        router = getattr(module, "router", None)
        if router:
            app.include_router(router)


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(
        "mock_main:app",
        host="localhost",
        port=8000,
        reload=True,
        log_config={
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "datefmt": "%Y-%m-%d %H:%M:%S",
                },
            },
            "handlers": {
                "default": {
                    "formatter": "default",
                    "class": "rich.logging.RichHandler",
                },
            },
            "root": {
                "level": "DEBUG",
                "handlers": ["default"],
            },
        }
    )
