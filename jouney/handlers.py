import random

from aiogram.dispatcher import FSMContext
from aiogram.types import Message, ContentType

from jouney.api_provider import OpenAIAPI
from jouney.bot import dp, bot

from jouney.config import config
from jouney.data import buttons, texts, prompts, States, phrases
from jouney.db import get_async_db
from jouney.narrator_provider import NarratorProvider
from jouney.story_manager import StoryManager
from jouney.user import UserDB
from jouney.utils import gen_keyboard, text

openai_api = OpenAIAPI(config.OPENAI_TOKEN)
narrators = NarratorProvider(bot, openai_api, phrases)


@dp.message_handler(commands=["help"], state="*")
async def help_handler(message: Message):
    await message.reply(texts["help"])


@dp.message_handler(commands=["start"], state="*")
async def start(message: Message, state: FSMContext):
    await message.answer(texts["intro"])
    await state.set_state(States.wait_story_desc)
    narrator = narrators.get_narrator(message.chat.id)
    if narrator is not None:
        narrator.cancel_loading()
    examples = random.choices(texts["examples"], k=4)
    await state.update_data(examples=examples)
    ask_setting_text = texts["start_story"]
    ask_setting_text += f"\n\n{texts['ask_story_setting']}\n\n" + "\n\n".join(
        [f"*{i + 1}.* {example}" for i, example in enumerate(examples)])
    btns = []
    for i, example in enumerate(examples):
        btns.append(f"{i + 1}")
    await message.answer(
        ask_setting_text,
        parse_mode="Markdown",
        reply_markup=gen_keyboard([btns, [buttons["skip_setting"]]])
    )


@dp.message_handler(regexp=r"\d", state=States.wait_story_desc)
async def select_example(message: Message, state: FSMContext):
    example_id = int(message.text) - 1
    examples = (await state.get_data())["examples"]
    story_setting = examples[example_id]
    await start_story(message, state, story_context=story_setting)


@dp.message_handler(text(buttons["skip_setting"]), state=States.wait_story_desc)
async def skip_setting(message: Message, state: FSMContext):
    await start_story(message, state)


@dp.message_handler(content_types=ContentType.TEXT, state=States.wait_story_desc)
async def have_story_description(message: Message, state: FSMContext):
    await start_story(message, state, story_context=message.text)


async def start_story(message: Message, state: FSMContext, story_context: str = None):
    await state.set_state(States.story)
    story = StoryManager(
        prompts["system_prompt"],
        prompts["assistant_reply"],
        openai_api
    )
    if story_context is not None:
        story.set_context(story_context)
    user = UserDB(message.chat.id, get_async_db())
    await user.create(message.from_user.full_name, message.from_user.username)
    narrator = narrators.create_narrator(message.chat.id, story, user)
    await narrator.start_story(prompts["start_story"], context_prompt=story_context)


@dp.message_handler(text(buttons["restart"]), state="*")
async def restart(message: Message, state: FSMContext):
    await state.set_state()
    await start(message, state)


@dp.message_handler(state=States.story)
async def option_handler(message: Message):
    narrator = narrators.get_narrator(message.chat.id)
    await narrator.iter_story(message.text)


@dp.message_handler(state="*")
async def default_handler(message: Message):
    await message.reply(texts["default"])
