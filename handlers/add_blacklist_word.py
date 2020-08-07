from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from misc import dp, controller


class AddBlacklistWordState(StatesGroup):
    word = State()


@dp.message_handler(commands="blacklist", state="*")
async def add_blacklist_step_1(message: types.Message):
    await message.answer("Please send word to block", reply_markup=types.ReplyKeyboardRemove())
    await AddBlacklistWordState.word.set()


@dp.message_handler(state=AddBlacklistWordState.word, content_types=types.ContentTypes.TEXT)
async def add_blacklist_step_2(message: types.Message, state: FSMContext):
    word = message.text.lower()
    await state.finish()
    if await controller.add_blacklist_word(word):
        await message.answer('Added successfully!')
    else:
        await message.answer('This word exist\'s in blacklist')
