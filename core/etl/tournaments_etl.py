import datetime
from typing import List

import httpx
from pydantic import BaseModel

from core.etl.abstract import AbstractETL
from database import SessionLocal
from models import Tournament


class TournamentDetail(BaseModel):
    battlefy_id: str
    start_time: datetime.datetime
    name: str
    region: str

    class Config:
        orm_mode = True


class TournamentsETL(AbstractETL):
    def __init__(self):
        self.date_start = datetime.datetime.utcnow().date()
        self.date_end = self.date_start + datetime.timedelta(weeks=8)

    async def _extract(self):
        url = f"https://majestic.battlefy.com/hearthstone-masters/tournaments?" \
              f"start={self.date_start.isoformat()}&end={self.date_end.isoformat()}"
        async with httpx.AsyncClient() as client:
            r = await client.get(url)
        return r.json()

    async def _transform(self, data: list) -> List[TournamentDetail]:
        return [TournamentDetail(
            battlefy_id=x['_id'],
            start_time=datetime.datetime.fromisoformat(x['startTime'][:-1]),
            name=x['name'],
            region=x['region'].upper(),
        ) for x in data]

    async def _load(self, data: List[TournamentDetail]) -> List[Tournament]:
        battlefy_ids = [x.battlefy_id for x in data]
        with SessionLocal() as session:
            in_db = {x for x, in session.query(Tournament).filter(
                Tournament.battlefy_id.in_(battlefy_ids)
            ).with_entities(Tournament.battlefy_id).all()}
            result = []
            for row in data:
                if row.battlefy_id in in_db:
                    continue
                tournament = Tournament(**row.dict())
                result.append(tournament)
                session.add(tournament)
            session.commit()
        return result
