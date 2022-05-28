import sqlalchemy as sa
from sqlalchemy.orm import relationship

from models.base import BaseModelORM


class TournamentPlayerDeck(BaseModelORM):
    __tablename__ = 'tournament_player_decks'

    tournament_player = relationship("TournamentPlayer")
    tournament_id = sa.Column(sa.ForeignKey("tournament_players.id"))
    deck_string = sa.Column(sa.String)
    archetype_predict = sa.Column(sa.String)
