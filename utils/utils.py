import json
import os
from typing import Dict
from typing import List

from aiogram.types import InlineKeyboardButton
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.markdown import code
from aiogram.utils.markdown import text

PATH = os.path.abspath(os.path.dirname(__file__))


def get_menu_kb(controller):
    """generate menu keyboard"""
    buttons = [
        InlineKeyboardButton('Update status', callback_data='menu1'),
        InlineKeyboardButton('Stop' if controller.is_working else 'Start', callback_data='menu2'),
        InlineKeyboardButton('Channels', callback_data='channels'),
        InlineKeyboardButton('Blacklist', callback_data='bl'),
    ]
    kb = InlineKeyboardMarkup()
    [kb.add(btn) for btn in buttons]
    return kb


def get_accepted_keys() -> Dict:
    """get displayable keys"""
    return {0: 'is_active', 1: 'send_video_post', 2: 'send_video_post_text', 3: 'send_photo_post',
            4: 'send_photo_post_text', 5: 'send_text_post',
            6: 'enable_filters'}


def get_blacklist_kb(controller, callback_name, page: int = None):
    """generate blacklist menu keyboard"""
    words = controller.db.get_blacklist_words(get_id=True)
    buttons = [InlineKeyboardButton(word['word'], callback_data=f'{callback_name}-{word["id"]}') for word in words]
    return paginate_channels_buttons(buttons, callback_name, page)


def get_channels_kb(controller, callback_name, page: int = None):
    """generate channels menu keyboard"""
    channels = controller.db.get_all_channels()
    buttons = [InlineKeyboardButton(f"{channel['vk_channel']} -> {channel['telegram_channel']}",
                                    callback_data=f"{callback_name}-{channel['id']}") for channel in channels]
    return paginate_channels_buttons(buttons, callback_name, page)


def paginate_channels_buttons(channels_buttons, callback_name, page: int = 0, pagination: int = 5):
    """generate paginated keyboard menu"""
    kb = InlineKeyboardMarkup()
    nav_buttons = [InlineKeyboardButton('ℹ Menu', callback_data='menu')]
    if channels_buttons:
        page_num = page if page else 0
        pages_list = []
        for i in range(0, len(channels_buttons), pagination):
            channels = channels_buttons[i:i + pagination]
            for channel in channels:
                channel.callback_data = f"{channel.callback_data}-{i}"
            pages_list.append(channels)
        pages_dict = {}
        [pages_dict.update({counter: page}) for counter, page in enumerate(pages_list)]
        [kb.add(button) for button in pages_dict.get(page_num)]
        if page_num:
            nav_buttons.append(InlineKeyboardButton('◀ Back', callback_data=f'{callback_name}-page-{page_num - 1}'))
        if page_num + 1 < len(pages_dict):
            nav_buttons.append(InlineKeyboardButton('▶ Next', callback_data=f'{callback_name}-page-{page_num + 1}'))
    return kb.row(*nav_buttons)


def get_bot_status(controller):
    """get status information"""
    tasks = controller.parser.channels_tasks
    active_channels = 'Running: *0/0*' if bool(controller.is_working) else ''
    if tasks:
        running_tasks = [1 for task_id, data in tasks.items() if not data['task'].done()]
        active_channels = f'Running: *{sum(running_tasks)}/{len(tasks)}*'

    working_status = '🟢' if bool(controller.is_working) else '🔴'

    msg = text(f'Working status: *{working_status}*',
               f"{active_channels}\n",
               f'Channels in db: *{len(controller.db.get_all_channels())}*',
               f'Words in blacklist: *{len(controller.parser.blacklist_words)}*',
               sep='\n')
    return msg


def get_channel_detail_kb(controller, channel_id):
    """generate channel detail keyboard menu"""
    channel_data = controller.db.get_channel(channel_id)
    kb = InlineKeyboardMarkup()
    if channel_data:
        channel = channel_data[0]

        accepted_keys = get_accepted_keys()
        for index, value in accepted_keys.items():
            name = ' '.join(value.split('_')).title()
            flag = 'On 🟢' if channel[value] else 'Off 🔴'
            callback_data = f'edit-{channel_id}-{index}'
            if value == 'is_active':
                kb.add(InlineKeyboardButton('Disable' if channel['is_active'] else 'Enable',
                                            callback_data=callback_data))
            else:
                kb.add(InlineKeyboardButton(f'{name}: {flag}', callback_data=callback_data))

        kb.row(InlineKeyboardButton('Set Last id', callback_data=f'edit-{channel_id}-97'),
               InlineKeyboardButton('♻ Reset Post id', callback_data=f'edit-{channel_id}-98'))

    kb.row(InlineKeyboardButton('⬅ Back', callback_data='channels'),
           InlineKeyboardButton('🗑️', callback_data=f'edit-{channel_id}-99'))
    return kb, code(json.dumps(format_channel_preview(channel_data[0]), indent=2))


def format_channel_preview(channel_data):
    """generate channel info text in channel detail menu"""
    return {'telegram_channel': channel_data['telegram_channel'], 'vk_channel': channel_data['vk_channel'],
            'last_post_id': get_preview_for_last_id(channel_data), 'timer': channel_data['timer']}


def get_preview_for_last_id(channel_data):
    """generate preview for last_post_id param"""
    return 'will set' if channel_data['set_last_post_id'] else channel_data['last_post_id']


async def normalize_channel_name(channel_name):
    """preparing telegram channel name"""
    is_num = channel_name.replace('-', '').isnumeric()
    return f'@{channel_name}' if not is_num else channel_name


async def get_post_url(channel_data: Dict, post: Dict) -> str:
    """create vk post url"""
    return f"https://vk.com/{channel_data['vk_channel']}?w=wall{post['from_id']}_{post['id']}"


async def clear_media_caption(medias: List):
    """clearing media caption"""
    medias_cleared = []
    for media in medias:
        media.caption = ''
        medias_cleared.append(media)
    return medias_cleared
