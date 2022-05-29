import asyncio
from typing import List, Optional

import httpx
from pydantic import BaseModel

from core.deck_strings import DeckStringCleaner
from core.etl.abstract import AbstractETL
from database import SessionLocal
from models import Tournament, TournamentPlayer, Player, TournamentPlayerDeck


class TournamentInfoError(Exception):
    pass


class DeckModel(BaseModel):
    deck_string: str
    deck_class: Optional[str]
    archetype_prediction: str


class TournamentPlayerModel(BaseModel):
    battle_tag: str
    decks: List[DeckModel]


class TournamentPlayersETL(AbstractETL):
    def __init__(self, tournament_id: str):
        self.tournament_id = tournament_id

    async def _extract(self):
        async with httpx.AsyncClient() as client:
            stages = await self._get_stages(client)
            first_round_matches = await client.get(f'https://dtmwra1jsgyb0.cloudfront.net/stages/{stages[0]}/'
                                                   f'matches?roundNumber=1')
            first_round_matches = first_round_matches.json()
            matches = []
            for m in first_round_matches:
                try:
                    top_player = m['top']['team']['name']
                except KeyError:
                    top_player = None
                try:
                    bottom_player = m['bottom']['team']['name']
                except KeyError:
                    bottom_player = None
                matches.append({'id': m['_id'], 'top': {'battle_tag': top_player, 'decks': []},
                                'bottom': {'battle_tag': bottom_player, 'decks': []}})
            tasks = []
            for match in matches:
                tasks.append(asyncio.ensure_future(self._get_deck_strings(client, match_id=match['id'])))
            deck_strings = await asyncio.gather(*tasks)
            for match, ds in zip(matches, deck_strings):
                try:
                    if match['top']['battle_tag']:
                        match['top']['decks'] = ds['top']
                except KeyError:
                    pass
                try:
                    if match['bottom']['battle_tag']:
                        match['bottom']['decks'] = ds['bottom']
                except KeyError:
                    pass
            return matches

    async def _get_stages(self, client: httpx.AsyncClient):
        request = await client.get(
            f'https://dtmwra1jsgyb0.cloudfront.net/tournaments/{self.tournament_id}?extend[stages]=true'
            f'&extend[organization]=true')
        response = request.json()
        if not isinstance(response, list) or len(response) == 0:
            raise TournamentInfoError
        stages = response[0]["stageIDs"]
        if len(stages) < 1:
            raise TournamentInfoError
        return stages

    async def _get_deck_strings(self, client: httpx.AsyncClient, match_id: str):
        url = f'https://majestic.battlefy.com/tournaments/{self.tournament_id}/matches/{match_id}/deckstrings'
        resp = await client.get(url)
        return resp.json()

    async def _transform(self, data):
        deck_strings, tasks, result = [], [], []
        async with httpx.AsyncClient() as client:
            for match in data:
                for p in ('top', 'bottom'):
                    if match[p]['battle_tag']:
                        clean_deck_strings = [DeckStringCleaner.clean_deck_string(x) for x in match['top']['decks']]
                        for cds in clean_deck_strings:
                            deck_strings.append(cds)
                            tasks.append(asyncio.ensure_future(self._get_archetype_predict(client, cds)))
            predictions = await asyncio.gather(*tasks, return_exceptions=True)
        deckstring_prediction = dict(zip(deck_strings, predictions))
        for match in data:
            for p in ('top', 'bottom'):
                if match[p]['battle_tag']:
                    clean_deck_strings = [DeckStringCleaner.clean_deck_string(x) for x in match['top']['decks']]
                    result.append(
                        TournamentPlayerModel
                        (battle_tag=match[p]['battle_tag'],
                         decks=[DeckModel(deck_string=x, archetype_prediction=str(deckstring_prediction[x]))
                                for x in clean_deck_strings])
                    )
        return result

    async def _get_archetype_predict(self, client: httpx.AsyncClient, deck_string: str) -> str:
        response = await client.post('http://144.21.40.16:6200/predict', json={'deckstring': deck_string})
        if response.status_code != 200:
            raise Exception
        return response.json()['prediction']

    async def _load(self, data: List[TournamentPlayerModel]) -> List[TournamentPlayer]:
        result = []
        player_battle_tags = {x.battle_tag for x in data}

        with SessionLocal() as session:
            players_in_db = session.query(Player).filter(Player.battletag.in_(player_battle_tags)).all()
            players_in_db = {p.battletag: p.id for p in players_in_db}

            tournament = session.query(Tournament).filter_by(battlefy_id=self.tournament_id).first()
            for row in data:
                if row.battle_tag in players_in_db:
                    player_id = players_in_db[row.battle_tag]
                else:
                    player = Player(battletag=row.battle_tag, nickname=row.battle_tag[:row.battle_tag.index('#')])
                    session.add(player)
                    session.commit()
                    players_in_db[row.battle_tag] = player.id
                    player_id = player.id
                tp = TournamentPlayer(player_id=player_id, tournament_id=tournament.id)
                session.add(tp)
                session.commit()
                result.append(tp)
                for deck in row.decks:
                    session.add(TournamentPlayerDeck(tournament_player=tp, deck_string=deck.deck_string,
                                                     archetype_predict=deck.archetype_prediction))
                    session.commit()
        return result
