import json
from typing import Dict
import aiohttp


class ApiUrls:
    """vk api urls"""
    wall = 'https://api.vk.com/method/wall.get'
    video = 'https://api.vk.com/method/video.get'


class VkApi:
    """provide vk api methods to get wall posts and video data"""
    def __init__(self, access_token: str):
        self._access_token = access_token

    @staticmethod
    async def _response_to_dict(data: aiohttp.ClientResponse) -> Dict:
        """convert vk response raw json to dict"""
        raw = await data.read()
        return json.loads(raw.decode('utf-8'))

    async def _get_post_response(self, session: aiohttp.ClientSession, url: str, data: Dict = None) -> Dict:
        """get response from post request"""
        data = dict() if not data else data
        data['access_token'] = self._access_token
        data['v'] = '5.120'
        async with session.post(url, data=data) as response:
            assert response.status == 200
            return await self._response_to_dict(response)

    async def _fetch(self, url: str, data: Dict = None) -> Dict:
        """get response from requested url"""
        async with aiohttp.ClientSession() as session:
            response = await self._get_post_response(session, url, data)
            return response

    async def get_wall_posts(self, channel: Dict, count: int = 5) -> Dict:
        """get vk wall posts"""
        data = {'domain': channel['vk_channel'], 'count': count, 'filter': 'owner'}
        return await self._fetch(ApiUrls.wall, data)

    async def get_video_data(self, video_id: str) -> Dict:
        """get video links"""
        data = {'videos': video_id, 'count': 1, 'extended': 1}
        return await self._fetch(ApiUrls.video, data)
