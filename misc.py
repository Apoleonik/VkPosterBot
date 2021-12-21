import os
import logging.config
from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from handlers.middleware import AccessMiddleware
from config import settings

from utils.controller import Controller

PATH = os.path.abspath(os.path.dirname(__file__))

logging.config.fileConfig(f'{PATH}/config/logging.config')
logger = logging.getLogger('main')


bot = Bot(token=settings.TELEGRAM_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())
dp.middleware.setup(AccessMiddleware(settings.ADMIN_ID, logger))

controller = Controller(settings.VK_TOKEN, bot, logger)
