import asyncio
import random

from .channel import MajsoulChannel
from .mjsoul import get_contest_management_servers

ACCESS_TOKEN = ''

class MajsoulClient(MajsoulChannel):
    def __init__(self, proto, log_messages=True):
        super().__init__(proto, log_messages)
    
    async def login(self):    
        res = await self.call(
            methodName = 'oauth2Login',
            type = 10,
            access_token = ACCESS_TOKEN,
        )
    
    async def fetch_game_log(self, uuid):
        res = await self.call(
            methodName = 'fetchGameRecord',
            game_uuid = uuid
        )

        return res

class ContestManagerClient(MajsoulChannel):
    def __init__(self, proto, log_messages=True):
        super().__init__(proto, log_messages)

        self._contest_players = []
        self._active_players = []
        self._ongoing_games = []

    @property
    async def contest_players(self):
        res = await self.call('fetchContestPlayer')

        self._contest_players = res.players

        return self._contest_players
    
    @property
    async def active_players(self):
        res = await self.call('startManageGame')
        
        self._active_players = res.players

        return self._active_players

    @property
    async def ongoing_games(self):
        res = await self.call('startManageGame')

        self._ongoing_games = res.games

        return self._ongoing_games

    async def login(self):    
        res = await self.call(
            methodName = 'oauth2LoginContestManager',
            type = 10,
            access_token = ACCESS_TOKEN,
            reconnect = True
        )
    
    async def get_game_id(self, nickname):
        '''
        find the game where the user with the given nickname is
        return the game id
        '''

        res = await self.call('startManageGame')
        
        for game in res.games:
            for player in game.players:
                if player.nickname == nickname:
                    return game.game_uuid

    async def pause(self, game_uuid):
        res = await self.call('pauseGame', uuid=game_uuid)
    
    async def unpause(self, game_uuid):
        res = await self.call('resumeGame', uuid=game_uuid)
    
    async def display_players(self, res=None):
        if res == None:
            res = await self.call('startManageGame')

        self._ongoing_games = res.games
        self._active_players = res.players

        numPlaying = sum([len(game.players) for game in res.games])
        numReady = len(res.players)

        response = f'''There are currently {numReady+numPlaying} player(s) in the lobby:\n'''
        response += f'{numReady} Ready, {numPlaying} In Game\n'
        response += '='*25 + '\n'

        if (numReady + numPlaying == 0):
            response += 'Wow, such empty...\n'

        playerNum = 0
        for game in res.games:
            t = "-"*40 + '\n'

            for player in game.players:
                playerNum += 1
                name = player.nickname
                t += f'{playerNum}. **(In Game) {player.nickname}\n**'

            response += t
        
        if numPlaying > 0:
            response += "-"*40 + '\n'
        
        for player in res.players:
            playerNum += 1
            name = player.nickname
            response += f'{playerNum}. {player.nickname}\n'
        
        response += "="*25
        
        return response

    async def get_player_nickname(self, playerID):
        res = await self.call('fetchContestPlayer')

        for player in res.players:
            if player.account_id == playerID:
                return player.nickname
        
        return None
    
    async def create_game(self, playerIDs):
        playerList = []
        for pid in playerIDs:
            playerList.append(self.proto.ReqCreateContestGame.Slot(account_id=pid))
            await self.call('lockGamePlayer', account_id=pid)
        res = await self.call(
            methodName='createContestGame',
            slots = playerList,
            random_position=True,
            open_live=True,
        )
    
    async def create_random_games(self):
        res = await self.call('startManageGame')

        players = res.players

        i = 0
        table = []
        while len(players) > 0:
            p = random.choice(players)
            players.remove(p)
            i += 1
            table.append(p.account_id)
            
            if i == 4:
                await self.create_game(table)
                i = 0

async def main():
    pass

if __name__ == "__main__":
    asyncio.run(main())