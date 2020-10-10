import os
import logging.config
from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from handlers.middleware import AccessMiddleware
from config import config

from utils.controller import Controller

PATH = os.path.abspath(os.path.dirname(__file__))

logging.config.fileConfig(f'{PATH}/config/logging.config')
logger = logging.getLogger('main')


bot = Bot(token=config.TELEGRAM_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())
dp.middleware.setup(AccessMiddleware(config.ADMIN_ID))

controller = Controller(config.VK_TOKEN, bot, logger)
