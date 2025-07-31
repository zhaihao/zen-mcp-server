import logging
from pathlib import Path

import orjson
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/looking-glass")


class DataModel(BaseModel):
    explore_type: str
    result: str


data: list[DataModel] = [DataModel(**item) for item in
                         orjson.loads((Path(__file__).parent / "router_explorer.json").read_bytes())]


@router.get('/router/explore')
def execute_router_explore(datacenter: str, explore_type: str, target_ip_or_domain: str):
    logging.info(f"router test {datacenter} {explore_type} {target_ip_or_domain}")
    for d in data:
        if d.explore_type.upper() == explore_type.upper():
            return d
    return None
