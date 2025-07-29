from pathlib import Path

import orjson
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/looking-glass")


class DataModel(BaseModel):
    city_a_code: str
    city_z_code: str
    delay: int


data: list[DataModel] = [DataModel(**item) for item in
                         orjson.loads((Path(__file__).parent / "sdn_city_delay_data.json").read_bytes())]


@router.get("/sdn/city/delay")
def get_city_delay(from_city: str, to_city: str):
    for d in data:
        if d.city_a_code == from_city.upper() and d.city_z_code == to_city.upper():
            return {"from_city": from_city, "to_city": to_city, "delay": f"{d.delay}ms"}
    return None
