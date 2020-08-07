import logging
from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from handlers.middleware import AccessMiddleware
from utils.controller import Controller

from config import config


controller = Controller(config.VK_TOKEN)

bot = Bot(token=config.TELEGRAM_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())
dp.middleware.setup(AccessMiddleware(config.ADMIN_ID))

logging.basicConfig(level=logging.INFO)
