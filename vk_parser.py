import asyncio
from typing import Dict, List, NamedTuple
from collections import defaultdict

from api import VkApi
from db import DbController


class Post(NamedTuple):
    """Contains parsed vk post"""
    id: int
    owner_id: int
    date: int
    text: str
    attachments: Dict


class VkParser(VkApi):
    def __init__(self, access_token: str):
        super().__init__(access_token)

        self.db = DbController()
        self.blacklist_words = self.db.get_blacklist_words()
        self.channels = self.db.get_all_channels()
        self.loop = asyncio.get_event_loop()

        self.channels_tasks = {}

    @staticmethod
    async def _parse_post_attachment(attachments: List[Dict]) -> Dict:
        """parse post attachments by type"""
        parsed_attachments = defaultdict(list)
        for attachment in attachments:
            attachment_type = attachment.get('type')
            if attachment_type == 'photo':
                parsed_attachments[attachment_type].append(attachment['photo']['sizes'][-1]['url'])
            elif attachment_type == 'video':
                video = attachment['video']
                video_id = f"{video['owner_id']}_{video['id']}_{video['access_key']}"
                parsed_attachments[attachment_type].append(video_id)
        return parsed_attachments

    async def _parse_post(self, data: Dict) -> Post:
        """parse post dict to Post entity"""
        attachments = await self._parse_post_attachment(data['attachments']) if data.get('attachments') else dict()
        return Post(id=data['id'], owner_id=data['owner_id'], date=data['date'],
                    text=data['text'], attachments=attachments)

    async def is_allowed_post(self, data: Dict) -> bool:
        """check post for blacklist words, advertisement and copyrights"""
        is_allowed_text = not bool([True for word in self.blacklist_words if word in data.get('text')])
        is_ads = data.get('marked_as_ads')
        is_shared = data.get('copyright')
        is_pinned = data.get('is_pinned')
        if is_allowed_text and not is_ads and not is_shared and not is_pinned:
            return True

    async def close_all_channels_tasks(self):
        """close all channels running tasks"""
        if self.channels_tasks:
            [data['task'].cancel() for task_id, data in self.channels_tasks.items()]
            self.channels_tasks.clear()

    async def close_channel_task(self, task_id: int):
        """close channel check task"""
        data = self.channels_tasks.get(task_id)
        if self.channels_tasks and data:
            data['task'].cancel()
            del self.channels_tasks[task_id]

    async def create_channel_task(self, channel_data: Dict):
        """create channel check task"""
        task = self.loop.create_task(self.check_channel(channel_data), name=channel_data['id'])
        self.channels_tasks[channel_data['id']] = {'channel_data': channel_data, 'task': task}

    async def check_channel(self, channel_data: Dict):
        """check vk channel for new posts and filter them, send content to telegram soon..."""
        # TODO оптимизация те создание очереди с постами, чтоб по кд не обращаться к апи ???
        # TODO отправка в телеграм через aiogram
        while True:
            wall_posts = await self.get_wall_posts(channel_data)
            is_correct = wall_posts.get('response') and wall_posts['response'].get('count')
            if is_correct:
                posts = wall_posts['response']['items']
                for post in reversed(posts):
                    post_id = int(post.get('id'))
                    if post_id > channel_data['last_post_id'] and await self.is_allowed_post(post):
                        channel_data['last_post_id'] = post_id

                        parsed_post = await self._parse_post(post)
                        photo_attachments = parsed_post.attachments.get('photo')
                        video_attachments = parsed_post.attachments.get('video')
                        if channel_data['send_photo_post'] and photo_attachments:
                            print(photo_attachments)
                            break
                        elif channel_data['send_video_post'] and video_attachments:
                            for video_id in video_attachments:
                                video_data = await self.get_video_data(video_id)
                                parsed_video_data = video_data['response']['items'][0]['files']
                                print(parsed_video_data)
                            break
                else:
                    print('no new posts')
                self.db.update_channel(channel_data['id'], channel_data)

            await asyncio.sleep(60 * channel_data['timer'])

    async def run(self):
        """start vk parser"""
        self.channels = self.db.get_all_channels()
        for channel in self.channels:
            if channel['is_active']:
                task = self.loop.create_task(self.check_channel(channel), name=channel['id'])
                self.channels_tasks[channel['id']] = {'channel_data': channel, 'task': task}

    async def stop(self):
        """stop vk parser"""
        await self.close_all_channels_tasks()

# TODO
#  1. 70% (добавить проверку на уникальность контента) дописать алгоритм для создания задач по проверке новых постов в группах вк
#  2. DONE добавить в стурктуру бд флаг 'Active' для канала
#  3. DONE (NOT TESTED) добавить функции для удаления и создания тасков для каждого канала по отдельности
#  4. создание
#  5. Отправка в телеграм через aiogram
