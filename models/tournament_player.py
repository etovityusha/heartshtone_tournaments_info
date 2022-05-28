import sqlalchemy as sa
from sqlalchemy.orm import relationship

from models.base import BaseModelORM


class TournamentPlayer(BaseModelORM):
    __tablename__ = 'tournament_players'

    tournament = relationship("Tournament")
    tournament_id = sa.Column(sa.ForeignKey("tournaments.id"))
    player = relationship("Player")
    player_id = sa.Column(sa.ForeignKey("players.id"))
