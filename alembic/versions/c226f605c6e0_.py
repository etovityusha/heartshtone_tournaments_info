"""empty message

Revision ID: c226f605c6e0
Revises: 82527c824c6c
Create Date: 2022-05-29 19:21:10.777560

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c226f605c6e0'
down_revision = '82527c824c6c'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('tournament_player_decks', sa.Column('tournament_player_id', sa.BigInteger(), nullable=True))
    op.drop_constraint('tournament_player_decks_tournament_id_fkey', 'tournament_player_decks', type_='foreignkey')
    op.create_foreign_key(None, 'tournament_player_decks', 'tournament_players', ['tournament_player_id'], ['id'])
    op.drop_column('tournament_player_decks', 'tournament_id')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('tournament_player_decks', sa.Column('tournament_id', sa.BIGINT(), autoincrement=False, nullable=True))
    op.drop_constraint(None, 'tournament_player_decks', type_='foreignkey')
    op.create_foreign_key('tournament_player_decks_tournament_id_fkey', 'tournament_player_decks', 'tournament_players', ['tournament_id'], ['id'])
    op.drop_column('tournament_player_decks', 'tournament_player_id')
    # ### end Alembic commands ###
