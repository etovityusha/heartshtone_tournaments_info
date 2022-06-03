import datetime
from typing import List

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, desc
from sqlalchemy.orm import Session

from database import get_db
from models import Tournament, TournamentPlayerDeck, TournamentPlayer

router = APIRouter(
    prefix="/tournaments",
    dependencies=[],
)


class TournamentListSerializer(BaseModel):
    id: int
    battlefy_id: str
    start_time: datetime.datetime
    name: str
    region: str
    status: str

    class Config:
        orm_mode = True


class ArchetypesSerializer(BaseModel):
    archetype: str
    count: int


class TournamentDetailsSerializer(BaseModel):
    archetypes: List[ArchetypesSerializer]


@router.get('/', response_model=List[TournamentListSerializer], tags=["tournaments"])
async def tournaments_list(date_from: datetime.date = None, date_to: datetime.date = None,
                           db: Session = Depends(get_db)):
    if not date_from or not date_to:
        now = datetime.datetime.utcnow()
        date_from = datetime.datetime.combine(
            (now - datetime.timedelta(days=now.weekday())).date(),
            datetime.time.min,
        )
        date_to = date_from + datetime.timedelta(days=7)
    tournaments = db.query(Tournament).filter(
        Tournament.start_time >= date_from,
        Tournament.start_time <= date_to,
    ).all()
    return tournaments


@router.get('/{battlefy_id}', response_model=TournamentDetailsSerializer, tags=['tournaments'])
async def tournament_stats(battlefy_id: str, db: Session = Depends(get_db)):
    counts = db.query(
        TournamentPlayerDeck.archetype_predict, func.count(TournamentPlayerDeck.id)
    ).join(TournamentPlayer).join(Tournament).filter(
        Tournament.battlefy_id == battlefy_id
    ).group_by(
        TournamentPlayerDeck.archetype_predict
    ).order_by(
        desc(func.count(TournamentPlayerDeck.id))
    ).all()
    return TournamentDetailsSerializer(archetypes=[ArchetypesSerializer(archetype=x[0], count=x[1]) for x in counts])
