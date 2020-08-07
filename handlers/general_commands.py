from aiogram import types
from aiogram.types.message import ParseMode

from misc import bot, dp, controller
import utils


@dp.message_handler(commands=['menu'])
async def display_menu(message: types.Message):
    kb = utils.get_menu_kb(controller)
    status = utils.get_bot_status(controller)
    await message.answer(status, reply_markup=kb, parse_mode=ParseMode.MARKDOWN_V2)


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('menu'))
async def process_callback_menu(callback_query: types.CallbackQuery):
    chat_id = callback_query.message.chat.id
    message_id = callback_query.message.message_id

    btn_code = callback_query.data[-1]
    if btn_code.isdigit():
        btn_code = int(btn_code)
    else:
        await bot.edit_message_text(text=utils.get_bot_status(controller), chat_id=chat_id,
                                    message_id=message_id, parse_mode=ParseMode.MARKDOWN_V2)
        await bot.edit_message_reply_markup(chat_id, message_id, reply_markup=utils.get_menu_kb(controller))

    if btn_code == 2:
        await controller.toggle_working()

    if btn_code == 1 or btn_code == 2:
        await bot.edit_message_text(text=utils.get_bot_status(controller), chat_id=chat_id,
                                    message_id=message_id, parse_mode=ParseMode.MARKDOWN_V2)
        await bot.edit_message_reply_markup(chat_id, message_id, reply_markup=utils.get_menu_kb(controller))
    else:
        await bot.answer_callback_query(callback_query.id)


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('channels'))
async def process_callback_channels(callback_query: types.CallbackQuery):
    chat_id = callback_query.message.chat.id
    message_id = callback_query.message.message_id

    btn_code = callback_query.data[-1]
    if btn_code.isdigit():
        btn_code = int(btn_code)

        kb, formatted_text = utils.get_channel_detail_kb(controller, btn_code)
        await bot.edit_message_text(text=formatted_text, chat_id=chat_id, message_id=message_id,
                                    parse_mode=ParseMode.MARKDOWN_V2)
        await bot.edit_message_reply_markup(chat_id, message_id, reply_markup=kb)
    else:
        await bot.edit_message_text(text=utils.get_bot_status(controller), chat_id=chat_id,
                                    message_id=message_id, parse_mode=ParseMode.MARKDOWN_V2)
        await bot.edit_message_reply_markup(chat_id, message_id, reply_markup=utils.get_channels_kb(controller))


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('edit'))
async def process_callback_channels(callback_query: types.CallbackQuery):
    chat_id = callback_query.message.chat.id
    message_id = callback_query.message.message_id

    _, channel_id, btn_code = callback_query.data.split('-')
    channel_data = controller.db.get_channel(int(channel_id))

    if btn_code.isdigit() and channel_data:
        channel = channel_data[0]
        btn_code = int(btn_code)
        accepted_keys = {0: 'is_active', 1: 'send_video_post', 2: 'send_video_post_text',
                         3: 'send_photo_post', 4: 'send_photo_post_text', 5: 'send_text_post'}

        key = accepted_keys.get(btn_code)
        if key:
            channel.update({key: not channel[key]})
            await controller.update_channel(channel['id'], channel)

        if not btn_code == 99:
            kb, formatted_text = utils.get_channel_detail_kb(controller, channel['id'])
            await bot.edit_message_text(text=formatted_text, chat_id=chat_id, message_id=message_id,
                                        parse_mode=ParseMode.MARKDOWN_V2)
            await bot.edit_message_reply_markup(chat_id, message_id, reply_markup=kb)
        else:
            await controller.remove_channel(channel)
            await bot.answer_callback_query(callback_query.id, 'Success channel delete!')
            await bot.edit_message_text(text=utils.get_bot_status(controller), chat_id=chat_id,
                                        message_id=message_id, parse_mode=ParseMode.MARKDOWN_V2)
            await bot.edit_message_reply_markup(chat_id, message_id, reply_markup=utils.get_menu_kb(controller))
    else:
        await bot.edit_message_reply_markup(chat_id, message_id, reply_markup=utils.get_channels_kb(controller))


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('bl'))
async def process_callback_channels(callback_query: types.CallbackQuery):
    chat_id = callback_query.message.chat.id
    message_id = callback_query.message.message_id

    btn_code = callback_query.data[-1]
    if btn_code.isdigit():
        btn_code = int(btn_code)
        await controller.remove_blacklist_word(btn_code)

    await bot.edit_message_text(text=utils.get_bot_status(controller), chat_id=chat_id,
                                message_id=message_id, parse_mode=ParseMode.MARKDOWN_V2)
    await bot.edit_message_reply_markup(chat_id, message_id, reply_markup=utils.get_blacklist_kb(controller))
