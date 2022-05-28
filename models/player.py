import sqlalchemy as sa

from models.base import BaseModelORM


class Player(BaseModelORM):
    __tablename__ = 'players'

    nickname = sa.Column(sa.String, nullable=False)
    battletag = sa.Column(sa.String, nullable=False, unique=True)
