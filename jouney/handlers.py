
from aiogram.dispatcher import FSMContext
from aiogram.types import Message, ContentType

from jouney.api_provider import OpenAIAPI
from jouney.bot import dp, bot

from jouney.config import config
from jouney.data import buttons, texts, prompts, States, phrases
from jouney.narrator import Narrator
from jouney.story_manager import StoryManager
from jouney.utils import gen_keyboard, text

openai_api = OpenAIAPI(config.OPENAI_TOKEN)


@dp.message_handler(commands=["start"], state="*")
async def start(message: Message, state: FSMContext):
    await message.answer(texts["intro"])
    await state.set_state(States.wait_story_desc)
    await message.answer(texts["start_story"], reply_markup=gen_keyboard([[buttons["skip_setting"]]]))


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
    await state.update_data({"story": story})
    narrator = Narrator(bot, message.chat.id, story, openai_api, phrases)
    await narrator.start_story(prompts["start_story"])


@dp.message_handler(text(buttons["restart"]), state=States.story)
async def restart(message: Message, state: FSMContext):
    await state.set_state()
    await start(message, state)


@dp.message_handler(state=States.story)
async def option_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    story = data.get("story")
    narrator = Narrator(bot, message.chat.id, story, openai_api, phrases)
    await narrator.iter_story(message.text)
    await state.update_data({"story": story})


@dp.message_handler(state="*")
async def default_handler(message: Message):
    await message.reply(texts["default"])
