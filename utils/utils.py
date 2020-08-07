import json
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.markdown import text, bold, italic, code, pre


def get_menu_kb(controller):
    buttons = [
        InlineKeyboardButton('Update status', callback_data='menu1'),
        InlineKeyboardButton('Stop' if controller.is_working else 'Start', callback_data='menu2'),
        InlineKeyboardButton('Channels', callback_data='channels'),
        InlineKeyboardButton('Blacklist', callback_data='bl'),
       ]
    kb = InlineKeyboardMarkup()
    [kb.add(btn) for btn in buttons]
    return kb


def get_blacklist_kb(controller):
    words = controller.db.get_blacklist_words(get_id=True)
    buttons = [InlineKeyboardButton(word['word'], callback_data=f'bl{word["id"]}') for word in words]
    kb = InlineKeyboardMarkup()
    [kb.add(btn) for btn in buttons]
    kb.add(InlineKeyboardButton('⬅ Back', callback_data='menu'))
    return kb


def get_bot_status(controller):
    msg = text(f'Is working: *{bool(controller.is_working)}*',
               f'Active channels: *{len(controller.parser.channels_tasks)}/{len(controller.db.get_all_channels())}*',
               f'Words in blacklist: *{len(controller.parser.blacklist_words)}*',
               sep='\n')
    return msg


def get_channels_kb(controller):
    channels_data = controller.db.get_all_channels()
    channels_buttons = []
    if channels_data:
        channels_buttons = [InlineKeyboardButton(f"{channel['vk_channel']} -> {channel['telegram_channel']}",
                                                 callback_data=f"channels{channel['id']}") for channel in channels_data]
    channels_buttons.append(InlineKeyboardButton('⬅ Back', callback_data='menu'))
    kb = InlineKeyboardMarkup()
    [kb.add(btn) for btn in channels_buttons]
    return kb


def get_channel_detail_kb(controller, channel_id):
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
            flag = 'On ✔' if channel[key] else 'Off ❌'
            buttons.append(InlineKeyboardButton(f'{name}: {flag}', callback_data=f'edit-{channel_id}-{index + 1}'))
        [kb.add(btn) for btn in buttons]
    kb.row(InlineKeyboardButton('⬅ Back', callback_data='channels'),
           InlineKeyboardButton('🗑️', callback_data=f'edit-{channel_id}-99'))
    return kb, code(json.dumps(channel_data[0], indent=2))

