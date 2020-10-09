import json
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.markdown import text, code


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
    active_channels = ''
    if tasks:
        running_tasks = [1 for task_id, data in tasks.items() if data['task'].done()]
        active_channels = f'Active channels: *{sum(running_tasks)}/{len(tasks)}*'

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
        accepted_keys = ['send_video_post', 'send_video_post_text',
                         'send_photo_post', 'send_photo_post_text', 'send_text_post']
        buttons = [InlineKeyboardButton('Disable' if channel['is_active'] else 'Enable',
                                        callback_data=f'edit-{channel_id}-0')]
        for index, key in enumerate(accepted_keys):
            name = ' '.join(key.split('_')).title()
            flag = 'On 🟢' if channel[key] else 'Off 🔴'
            buttons.append(InlineKeyboardButton(f'{name}: {flag}', callback_data=f'edit-{channel_id}-{index + 1}'))
        [kb.add(btn) for btn in buttons]
        kb.add(InlineKeyboardButton('♻ Reset Post id', callback_data=f'edit-{channel_id}-98'))

    kb.row(InlineKeyboardButton('⬅ Back', callback_data='channels'),
           InlineKeyboardButton('🗑️', callback_data=f'edit-{channel_id}-99'))
    return kb, code(json.dumps(format_channel_preview(channel_data[0]), indent=2))


def format_channel_preview(channel_data):
    """generate channel info text in channel detail menu"""
    return {'telegram_channel': channel_data['telegram_channel'], 'vk_channel': channel_data['vk_channel'],
            'last_post_id': channel_data['last_post_id'], 'timer': channel_data['timer']}


async def normalize_channel_name(channel_name):
    """preparing telegram channel name"""
    return '@'.join(channel_name) if not channel_name.isdigit() else channel_name
