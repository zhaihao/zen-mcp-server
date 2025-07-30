from pathlib import Path

import orjson
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/looking-glass")


class DataModel(BaseModel):
    city_a_code: str
    city_z_code: str
    delay: int


sdn_data: list[DataModel] = [DataModel(**item) for item in
                             orjson.loads((Path(__file__).parent / "sdn_city_delay_data.json").read_bytes())]
public_data: list[DataModel] = [DataModel(**item) for item in
                                orjson.loads((Path(__file__).parent / "public_network_delay.json").read_bytes())]


@router.get("/city/delay")
def get_city_delay(from_city: str, to_city: str):
    res = {"from_city": from_city, "to_city": to_city,"private_line_delay":'no data provide','public_network_delay':'no data provide'}
    for d in sdn_data:
        if d.city_a_code == from_city.upper() and d.city_z_code == to_city.upper():
            res.update({"private_line_delay":f'{d.delay}ms'})

    for d in public_data:
        if d.city_a_code == from_city.upper() and d.city_z_code == to_city.upper():
            res.update({"public_network_delay":f'{d.delay}ms'})

    return res
