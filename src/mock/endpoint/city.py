from pathlib import Path

import orjson
from fastapi import APIRouter
from pydantic import BaseModel


class CityModel(BaseModel):
    city_code: str
    city_name: str
    city_name_en: str
    country_name: str
    country_name_en: str


data: list[CityModel] = [CityModel(**item) for item in
                         orjson.loads((Path(__file__).parent / "cities.json").read_bytes())]

router = APIRouter(prefix="/looking-glass")


@router.get("/city")
def get_city_code(city_name_en: str):
    for d in data:
        if d.city_name_en.upper() == city_name_en.upper():
            return d
    return None
