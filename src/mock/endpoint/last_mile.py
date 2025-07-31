from pathlib import Path

import orjson
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/looking-glass")


class DataModel(BaseModel):
    agent_city_code: str
    eye_city_name: str
    eye_country_name: str
    org_name: str
    asn: str
    delay: float


data: list[DataModel] = [DataModel(**item) for item in
                         orjson.loads((Path(__file__).parent / "last_mile.json").read_bytes())]


@router.get('/eyeball/coverage')
def get_city_eyeball_coverage(city: str):
    res = []
    for d in data:
        if d.agent_city_code.upper() == city.upper():
            res.append(d)
    return res
