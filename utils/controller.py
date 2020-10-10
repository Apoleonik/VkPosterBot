from typing import Dict

from utils.vk_parser import VkParser


class Controller:
    def __init__(self, access_token: str, telegram_bot, logger):
        self.parser = VkParser(access_token, telegram_bot, logger)
        self.db = self.parser.db
        self.logger = logger
        self.is_working = False

    async def toggle_working(self):
        """toggle parser working"""
        if self.is_working:
            await self.stop_parser()
            self.logger.info('Parser stopped')
        else:
            await self.start_parser()
            self.logger.info('Parser successfully started')

    async def start_parser(self):
        """start parser"""
        if not self.is_working:
            await self.parser.run()
            self.is_working = True

    async def stop_parser(self):
        """stop parser"""
        await self.parser.stop()
        self.is_working = False

    async def add_channel(self, channel_data: Dict):
        """add channel to db and create parse task"""
        self.db.add_channel(channel_data)
        db_channel_data = self.db.get_channel_by_tg_vk_channel_key(channel_data['telegram_channel'],
                                                                   channel_data['vk_channel'])
        if self.is_working and db_channel_data and db_channel_data[0]['is_active']:
            await self.parser.create_channel_task(db_channel_data[0])
        self.logger.info(f'Add new channel {channel_data["vk_channel"]} -> {channel_data["telegram_channel"]}')

    async def remove_channel(self, channel_data: Dict):
        """remove channel from db and stop task"""
        self.db.delete_channel(channel_data['id'])
        await self.parser.close_channel_task(channel_data['id'])
        self.logger.info(f'Remove channel {channel_data["vk_channel"]} -> {channel_data["telegram_channel"]} from db')

    async def update_channel(self, row_id: int, channel_data: Dict):
        """update channel info and restart task"""
        self.db.update_channel(row_id, channel_data)
        await self.parser.close_channel_task(row_id)

        db_channel_data = self.db.get_channel(row_id)
        if self.is_working and db_channel_data and db_channel_data[0]['is_active']:
            await self.parser.create_channel_task(db_channel_data[0])
        self.logger.info(f'Updated {channel_data["vk_channel"]} (id: {channel_data["id"]}) params')

    async def add_blacklist_word(self, word: str):
        """add blacklist word to db and parser"""
        black_list_words = self.db.get_blacklist_words()
        if word.lower() not in black_list_words:
            self.db.add_blacklist_word(word.lower())
            self.parser.blacklist_words.append(word.lower())
            self.logger.info(f'Add "{word}" word to blacklist')
            return True

    async def remove_blacklist_word(self, row_id: int):
        """remove blacklist word from db and parser"""
        self.db.delete_blacklist_word(row_id)
        black_list_words = self.db.get_blacklist_words()
        self.parser.blacklist_words = black_list_words
        self.logger.info(f'Removed word from blacklist')
