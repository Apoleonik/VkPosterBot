from aiogram import executor
import handlers
from misc import dp, logger


if __name__ == '__main__':
    logger.info('Start telegram bot')
    executor.start_polling(dp, skip_updates=True)


# TODO
#  1. 70% (добавить проверку на уникальность контента) дописать алгоритм для создания задач по проверке новых постов в группах вк
#  2. DONE добавить в стурктуру бд флаг 'Active' для канала
#  3. DONE (NOT TESTED) добавить функции для удаления и создания тасков для каждого канала по отдельности
#  5. DONE Отправка в телеграм через aiogram
#  6. DONE Добавить постраничную навигацию
#  7. DONE Добавить логгирование
#  8. оптимизация те создание очереди с постами, чтоб по кд не обращаться к апи ???
