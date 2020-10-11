from aiogram import types
from aiogram.dispatcher.handler import CancelHandler
from aiogram.dispatcher.middlewares import BaseMiddleware


class AccessMiddleware(BaseMiddleware):
    def __init__(self, access_id: int, logger):
        self.access_id = access_id
        self.logger = logger
        super().__init__()

    async def on_process_message(self, message: types.Message, _):
        if message['text'].startswith('/'):
            self.logger.info(f'[MESSAGE] | Got "{message["text"]}" message from: {message["from"]["username"]}')
        if int(message.from_user.id) != int(self.access_id):
            await message.answer("Sorry, you doesn\'t have access!")
            raise CancelHandler()
