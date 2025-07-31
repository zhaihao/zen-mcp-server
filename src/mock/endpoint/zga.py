import logging
from pathlib import Path

import orjson
from fastapi import APIRouter
from pydantic import BaseModel, computed_field

router = APIRouter(prefix="/looking-glass")


class DataModel(BaseModel):
    via_public_internet_delay: int
    via_zga_delay: int
    target: str

    @computed_field
    @property
    def improvement_percentage(self) -> str:
        improvement = (self.via_public_internet_delay - self.via_zga_delay) / self.via_public_internet_delay
        return f"{improvement * 100:.0f}%"


data: list[DataModel] = [DataModel(**item) for item in
                         orjson.loads((Path(__file__).parent / "zga.json").read_bytes())]


@router.get("/zga/test")
def get_city_delay(city):
    logging.info(f'zga test {city}')
    res = []
    for d in data:
        res.append({
            "via_public_internet_delay": f'{d.via_public_internet_delay}ms',
            "via_zga_delay": f'{d.via_zga_delay}ms',
            "target": d.target,
            "improvement_percentage": d.improvement_percentage
        })

    return res
