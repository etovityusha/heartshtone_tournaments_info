import enum

import sqlalchemy as sa

from models.base import BaseModelORM


class Tournament(BaseModelORM):
    class RegionEnum(str, enum.Enum):
        ASIA = 'ASIA'
        EUROPE = 'EUROPE'
        AMERICAS = 'AMERICAS'

    __tablename__ = 'tournaments'

    battlefy_id = sa.Column(sa.String, nullable=False)
    start_time = sa.Column(sa.DateTime, nullable=False)
    name = sa.Column(sa.String, nullable=False)
    region = sa.Column(sa.Enum(RegionEnum), default=RegionEnum.EUROPE, nullable=False)
