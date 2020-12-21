import asyncio
from collections import defaultdict
from typing import Dict
from typing import List
from typing import NamedTuple

from aiogram import Bot
from aiogram.types import InputMediaPhoto
from aiogram.types import InputMediaVideo

from config.config import ADMIN_ID
from utils.api import VkApi
from utils.db import DbController
from utils.utils import clear_media_caption
from utils.utils import get_post_url
from utils.utils import normalize_channel_name


class Post(NamedTuple):
    """Contains parsed vk post"""
    id: int
    owner_id: int
    date: int
    text: str
    attachments: Dict


class VkParser(VkApi):
    def __init__(self, access_token: str, bot: Bot, logger):
        super().__init__(access_token)

        self.bot = bot
        self.logger = logger
        self.db = DbController()
        self.blacklist_words = self.db.get_blacklist_words()
        self.channels = self.db.get_all_channels()
        self.loop = asyncio.get_event_loop()

        self.channels_tasks = {}

    async def _parse_post_attachment(self, attachments: List[Dict]) -> Dict:
        """parse post attachments by type"""
        parsed_attachments = defaultdict(list)
        for attachment in attachments:
            attachment_type = attachment.get('type')
            if attachment_type == 'photo':
                parsed_attachments[attachment_type].append(attachment['photo']['sizes'][-1]['url'])
            elif attachment_type == 'video':
                parsed_video = await self._parse_video(attachment)
                if parsed_video['platform'] == 'youtube':
                    parsed_attachments['link'].append(parsed_video) if parsed_video['url'] else ''
                else:
                    parsed_attachments[attachment_type].append(parsed_video['id'])
            elif attachment_type == 'link':
                link = attachment['link']
                link_title = await self._prepare_markdown_text(link['title']) if link.get('title') else 'link'
                parsed_attachments[attachment_type].append({'title': link_title, 'url': link['url']})
        return parsed_attachments

    async def _parse_post(self, data: Dict) -> Post:
        """parse post dict to Post entity"""
        attachments = await self._parse_post_attachment(data['attachments']) if data.get('attachments') else dict()
        return Post(id=data['id'], owner_id=data['owner_id'], date=data['date'],
                    text=data['text'], attachments=attachments)

    async def _parse_video(self, video_data: Dict) -> Dict:
        """parse video from vk api json"""
        video = video_data['video']
        video_title = 'video' if not video.get('title') else await self._prepare_markdown_text(video['title'])
        video_id = f"{video['owner_id']}_{video['id']}_{video['access_key']}"
        video_platform = video.get('platform').lower() if video.get('platform') else ''
        video_data = await self.get_video_data(video_id)
        video_url = video_data['response']['items'][0]['files'].get('external')
        return {'title': video_title, 'url': video_url if video_url else '',
                'platform': video_platform, 'id': video_id}

    @staticmethod
    async def _prepare_markdown_text(text: str) -> str:
        """convert text to markdown"""
        return text.replace('[', '(').replace(']', ')')

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
        self.logger.debug(f'Closed channel task with id: {task_id}')

    async def create_channel_task(self, channel_data: Dict):
        """create channel check task"""
        task = self.loop.create_task(self.check_channel(channel_data), name=channel_data['id'])
        self.channels_tasks[channel_data['id']] = {'channel_data': channel_data, 'task': task}
        self.logger.debug(f'Created channel task for {channel_data["telegram_channel"]} (id: {channel_data["id"]})')

    @staticmethod
    async def set_last_post_id(channel_data: Dict, posts: List):
        """set last post id in channel_data"""
        if channel_data['set_last_post_id']:
            posts_id = [post['id'] for post in posts]
            posts_id.sort()
            channel_data['last_post_id'] = posts_id[-1]
            channel_data['set_last_post_id'] = 0
        return channel_data

    async def check_channel(self, channel_data: Dict):
        """check vk channel for new posts and filter them"""
        while True:
            wall_posts = await self.get_wall_posts(channel_data)
            is_correct = wall_posts.get('response') and wall_posts.get('response').get('count')
            if is_correct:
                posts = wall_posts['response']['items']
                channel_data = await self.set_last_post_id(channel_data, posts)
                for post in reversed(posts):
                    post_id = int(post.get('id'))
                    is_allowed_post = True if not channel_data['enable_filters'] else await self.is_allowed_post(post)
                    if post_id > channel_data['last_post_id'] and is_allowed_post:
                        channel_data['last_post_id'] = post_id
                        parsed_post = await self._parse_post(post)
                        post_url = await get_post_url(channel_data, post)
                        prepared_content = await self.prepare_content(channel_data, parsed_post)
                        if prepared_content:
                            self.logger.info(f'Found new post from {channel_data["vk_channel"]} -> '
                                             f'{channel_data["telegram_channel"]}')
                            await self.send_content(channel_data, prepared_content, post_url)
                            break
                else:
                    self.logger.info(f'No new posts from {channel_data["vk_channel"]}')
                self.db.update_channel(channel_data['id'], channel_data)
            else:
                self.logger.info(f'No correct posts for {channel_data["vk_channel"]}')
                await self.bot.send_message(ADMIN_ID, f'Error: {wall_posts.get("error").get("error_msg")}')

            await asyncio.sleep(60 * int(channel_data['timer']) if channel_data['timer'] else 60 * 60)

    async def prepare_content(self, channel_data, parsed_post):
        """prepare post content before send to telegram channel"""
        prepared_content = {}
        post_text = parsed_post.text
        photo_text = parsed_post.text if channel_data['send_photo_post_text'] else ''
        video_text = parsed_post.text if channel_data['send_video_post_text'] else ''
        photo_attachments = parsed_post.attachments.get('photo')
        video_attachments = parsed_post.attachments.get('video')
        link_attachments = parsed_post.attachments.get('link')
        if channel_data['send_photo_post'] and photo_attachments:
            prepared_photo = [InputMediaPhoto(photo) for photo in photo_attachments]
            prepared_photo[0].caption = photo_text
            prepared_content.update({'photo': prepared_photo})
        elif channel_data['send_video_post'] and video_attachments:
            prepared_video = {}
            for video_id in video_attachments:
                video_data = await self.get_video_data(video_id)
                parsed_video_data = video_data['response']['items'][0]['files']
                prepared_video = {quality: InputMediaVideo(video, caption=video_text)
                                  for quality, video in parsed_video_data.items()}
            prepared_content.update({'video': prepared_video})
        elif channel_data['send_text_post'] and post_text and not (photo_text and video_text):
            prepared_content.update({'text': post_text})
        elif not channel_data['enable_filters'] and link_attachments:
            links = [f'[{link["title"]}]({link["url"]})\n' for link in link_attachments if link["url"] not in post_text]
            prepared_content.update({'text': '\n'.join([' |'.join(links), post_text])})
        return prepared_content

    async def send_content(self, channel_data: Dict, prepared_content: Dict, post_url: str):
        """send content to telegram"""
        telegram_channel = await normalize_channel_name(channel_data['telegram_channel'])
        while prepared_content.get('video') or prepared_content.get('photo') or prepared_content.get('text'):
            content_to_send = []
            for content_type, content in prepared_content.items():
                if content_type == 'video':
                    quality, video = prepared_content.get('video').popitem()
                    content_to_send.append(video)
                elif content_type == 'photo':
                    content_to_send.extend(content)
                elif content_type == 'text':
                    content_to_send.append(content)
            try:
                content = content_to_send[0]
                media_text_limit = 1024
                message_text_limit = 4096

                if not isinstance(content, str):
                    text = content.caption
                    if len(text) > media_text_limit:
                        cleared_media_group = await clear_media_caption(content_to_send)
                        media_message = await self.bot.send_media_group(telegram_channel, cleared_media_group)
                        await media_message.pop().reply(text[:message_text_limit], disable_web_page_preview=True)
                        break
                    else:
                        await self.bot.send_media_group(telegram_channel, content_to_send)
                        break
                else:
                    await self.bot.send_message(telegram_channel, content, parse_mode='MARKDOWN')
                    break
            except Exception as error:
                self.logger.error(f"While sending post {post_url}: {error}")
                text = f'***Post:*** [link]({post_url})\n***Error:*** {error} '
                if not prepared_content.get('video'):
                    await self.bot.send_message(ADMIN_ID, text, parse_mode='MARKDOWN', disable_web_page_preview=True)
                    break
                await asyncio.sleep(5)

    async def run(self):
        """start vk parser"""
        self.channels = self.db.get_all_channels()
        for channel in self.channels:
            if channel['is_active']:
                task = self.loop.create_task(self.check_channel(channel), name=channel['id'])
                self.channels_tasks[channel['id']] = {'channel_data': channel, 'task': task}
                self.logger.debug(f'Started task for {channel["vk_channel"]} -> {channel["telegram_channel"]}')

    async def stop(self):
        """stop vk parser"""
        await self.close_all_channels_tasks()
