import asyncio
import datetime
from typing import List

import httpx
from pydantic import BaseModel

from core.deck_strings import DeckStringCleaner
from core.etl.abstract import AbstractETL
from database import SessionLocal
from models import Tournament


class TournamentInfoError(Exception):
    pass


class DeckModel(BaseModel):
    deck_string: str
    deck_class: str
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
                if match['top']['battle_tag']:
                    match['top']['decks'] = ds['top']
                if match['bottom']['battle_tag']:
                    match['bottom']['decks'] = ds['bottom']
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
        pass

    async def _get_archetype_predict(self, client: httpx.AsyncClient, deck_string: str):
        pass

    async def _load(self, data):
        with SessionLocal() as session:
            pass
        return data
