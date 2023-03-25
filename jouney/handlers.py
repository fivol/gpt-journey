import random

from aiogram.dispatcher import FSMContext
from aiogram.types import Message, ContentType
from loguru import logger

from jouney.api_provider import OpenAIAPI
from jouney.bot import dp, bot

from jouney.config import config
from jouney.data import States, DataProvider, data_en, data_ru
from jouney.db import get_async_db
from jouney.narrator_provider import NarratorProvider
from jouney.story_manager import StoryManager
from jouney.user import UserDB
from jouney.utils import gen_keyboard, text

openai_api = OpenAIAPI(config.OPENAI_TOKEN)
narrators = NarratorProvider(bot, openai_api)


async def get_data_provider(state: FSMContext, chat_id: int) -> DataProvider:
    data = await state.get_data() or {}
    if "lang" not in data:
        user = UserDB(chat_id, get_async_db())
        lang = (await user.get_user())["lang"]
    else:
        lang = data["lang"]
    return DataProvider(lang)


@dp.message_handler(commands=["help"], state="*")
async def help_handler(message: Message, state: FSMContext):
    help_text = (await get_data_provider(state, message.chat.id)).texts["help"]
    await message.reply(help_text)


@dp.message_handler(commands=["reset"], state="*")
async def reset_handler(message: Message, state: FSMContext):
    await UserDB(message.chat.id, get_async_db()).remove_lang()
    await before_start(message, state)


@dp.message_handler(text(data_en.buttons["lang_en"], data_en.buttons["lang_ru"]), state="*")
async def select_len(message: Message, state: FSMContext):
    if message.text == data_en.buttons["lang_en"]:
        lang = "en"
    else:
        lang = "ru"
    await state.update_data({"lang": lang})

    await UserDB(message.chat.id, get_async_db()).set_lang(lang)

    await start(message, state)


@dp.message_handler(commands=["start"], state="*")
async def before_start(message: Message, state: FSMContext):
    narrators.remove_narrator(message.chat.id)
    user = await UserDB(message.chat.id, get_async_db()).get_user()
    if user is None or user["lang"] is None:
        await message.answer(data_en.texts["select_language"],
                             reply_markup=gen_keyboard([[data_en.buttons["lang_en"], data_en.buttons["lang_ru"]]]))
    else:
        await state.update_data({"lang": user["lang"]})
        await start(message, state)


@dp.message_handler(commands=["start"], state="*")
async def start(message: Message, state: FSMContext):
    lang = (await state.get_data())["lang"]
    data = DataProvider(lang)
    await message.answer(data.texts["intro"])
    await state.set_state(States.wait_story_desc)
    narrator = narrators.get_narrator(message.chat.id)
    if narrator is not None:
        narrator.cancel_loading()
    examples = random.choices(data.texts["examples"], k=4)
    await state.update_data(examples=examples)
    ask_setting_text = data.texts["start_story"]
    ask_setting_text += f"\n\n{data.texts['ask_story_setting']}\n\n" + "\n\n".join(
        [f"*{i + 1}.* {example}" for i, example in enumerate(examples)])
    btns = []
    for i, example in enumerate(examples):
        btns.append(f"{i + 1}")
    await message.answer(
        ask_setting_text,
        parse_mode="Markdown",
        reply_markup=gen_keyboard([btns, [data.buttons["skip_setting"]]])
    )


@dp.message_handler(regexp=r"\d", state=States.wait_story_desc)
async def select_example(message: Message, state: FSMContext):
    example_id = int(message.text) - 1
    examples = (await state.get_data())["examples"]
    data = await get_data_provider(state, message.chat.id)
    try:
        story_setting = examples[example_id]
        await start_story(message, state, story_context=story_setting)

    except IndexError:
        await message.answer(data.texts["wrong_option"])


@dp.message_handler(text(data_en.buttons["skip_setting"], data_ru.buttons["skip_setting"]),
                    state=States.wait_story_desc)
async def skip_setting(message: Message, state: FSMContext):
    await start_story(message, state)


@dp.message_handler(content_types=ContentType.TEXT, state=States.wait_story_desc)
async def have_story_description(message: Message, state: FSMContext):
    await start_story(message, state, story_context=message.text)


async def start_story(message: Message, state: FSMContext, story_context: str = None):
    await state.set_state(States.story)
    lang = (await state.get_data())["lang"]
    data = DataProvider(lang)
    story = StoryManager(
        data.prompts["system_prompt"],
        data.prompts["assistant_reply"],
        openai_api
    )
    if story_context is not None:
        story.set_context(story_context)
    user = UserDB(message.chat.id, get_async_db())
    await user.create(message.from_user.full_name, message.from_user.username, lang)
    narrator = narrators.create_narrator(message.chat.id, story, user, data)
    await narrator.start_story(data.prompts["start_story"], context_prompt=story_context)


@dp.message_handler(text(data_en.buttons["restart"], data_ru.buttons["restart"]), state="*")
async def restart(message: Message, state: FSMContext):
    await state.set_state()
    await start(message, state)


@dp.message_handler(regexp=r"\d", state=States.story)
async def option_handler(message: Message, state: FSMContext):
    narrator = narrators.get_narrator(message.chat.id)
    try:
        await narrator.iter_story(message.text)
    except IndexError:
        await message.reply(narrator.data.texts["wrong_option"])
    except:
        logger.exception("Error in option_handler")
        await default_handler(message, state)


@dp.message_handler(state="*")
async def default_handler(message: Message, state: FSMContext):
    lang = (await state.get_data())["lang"]
    data = DataProvider(lang)
    await message.reply(data.texts["default"])
