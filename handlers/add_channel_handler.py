from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.utils.markdown import text, bold
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types.message import ParseMode


from misc import dp, controller


class AddChannelState(StatesGroup):

    vk_channel = State()
    telegram_channel = State()
    timer = State()
    is_active = State()
    send_video_post = State()
    send_video_post_text = State()
    send_photo_post = State()
    send_photo_post_text = State()
    send_text_post = State()


def get_true_false_kb():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row(types.KeyboardButton('True'), types.KeyboardButton('False'))
    return keyboard


@dp.message_handler(commands="add", state="*")
async def add_channel_step_1(message: types.Message):
    await message.answer(text("Please send", bold('vk_channel'), "name"), parse_mode=ParseMode.MARKDOWN_V2,
                         reply_markup=types.ReplyKeyboardRemove())
    await AddChannelState.vk_channel.set()


@dp.message_handler(state=AddChannelState.vk_channel, content_types=types.ContentTypes.TEXT)
async def add_channel_step_2(message: types.Message, state: FSMContext):
    await state.update_data(vk_channel=message.text.lower())
    await AddChannelState.telegram_channel.set()
    await message.answer(text("Send", bold("telegram_channel"), "where bot will post"), parse_mode=ParseMode.MARKDOWN_V2)


@dp.message_handler(state=AddChannelState.telegram_channel, content_types=types.ContentTypes.TEXT)
async def add_channel_step_3(message: types.Message, state: FSMContext):
    await state.update_data(telegram_channel=''.join(message.text.lower().split('@')))
    await AddChannelState.timer.set()
    await message.answer(text("Send channel", bold("timer")), parse_mode=ParseMode.MARKDOWN_V2)


@dp.message_handler(state=AddChannelState.timer, content_types=types.ContentTypes.TEXT)
async def add_channel_step_4(message: types.Message, state: FSMContext):
    if message.text.isdigit() and int(message.text) >= 5:
        await state.update_data(timer=int(message.text.lower()))
        await AddChannelState.is_active.set()
        await message.answer("Will channel be enabled instantly?", reply_markup=get_true_false_kb())
    else:
        await message.reply("Please enter integer that will be more then 5!")


@dp.message_handler(state=AddChannelState.is_active, content_types=types.ContentTypes.TEXT)
@dp.message_handler(state=AddChannelState.send_video_post, content_types=types.ContentTypes.TEXT)
@dp.message_handler(state=AddChannelState.send_video_post_text, content_types=types.ContentTypes.TEXT)
@dp.message_handler(state=AddChannelState.send_photo_post, content_types=types.ContentTypes.TEXT)
@dp.message_handler(state=AddChannelState.send_photo_post_text, content_types=types.ContentTypes.TEXT)
@dp.message_handler(state=AddChannelState.send_text_post, content_types=types.ContentTypes.TEXT)
async def add_channel_steps(message: types.Message, state: FSMContext):
    if message.text not in ('True', 'False'):
        await message.reply('Please choose by keyboard!')
        return

    current_state = await state.get_state()
    current_state_name = current_state.split(':')[-1]

    await state.update_data({current_state_name: eval(message.text)})
    next_state = await AddChannelState.next()
    if next_state:
        await message.answer(text('Flag for', bold(text(next_state.split(':')[-1] + '?'))),
                             parse_mode=ParseMode.MARKDOWN_V2, reply_markup=get_true_false_kb())
    else:
        channel_data = await state.get_data()
        await controller.add_channel(channel_data)
        await message.answer(text(f'Successfully added {channel_data["vk_channel"]} channel'),
                             parse_mode=ParseMode.MARKDOWN_V2, reply_markup=types.ReplyKeyboardRemove())
