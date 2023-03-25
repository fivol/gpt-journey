import asyncio
import io
import os
import random

import aiohttp
from aiogram.types import InputFile, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from loguru import logger
from pydantic import BaseModel

from jouney.api_provider import OpenAIAPI
from jouney.data import buttons
from jouney.story_manager import StoryManager
from jouney.user import UserDB
from jouney.utils import gen_keyboard


class TmpMessage(BaseModel):
    wait_phrase_msg: int
    hourglass_msg: int


class Narrator:
    def __init__(self, bot, chat_id: int, story: StoryManager, openai_api: OpenAIAPI,
                 user: UserDB, wait_phrases: list[str] = None):
        self._chat_id = chat_id
        self._bot = bot
        self._story = story
        self._user = user
        self._openai_api = openai_api
        self._wait_phrases = wait_phrases
        self._load_tasks = []
        self._current_options = []
        self._story_id = None
        self._story_item_id = None
        self._img_content = {}

    def cancel_loading(self):
        for opt, task in self._load_tasks:
            task.cancel()
        self._load_tasks = []

    async def _send_wait_phrase(self) -> TmpMessage:
        wait_phrase = self._select_wait_phrase()
        phrase_msg = await self._bot.send_message(self._chat_id, wait_phrase)
        hourglass_msg = await self._bot.send_message(self._chat_id, "⏳", reply_markup=ReplyKeyboardRemove())
        msg = TmpMessage(
            wait_phrase_msg=phrase_msg.message_id,
            hourglass_msg=hourglass_msg.message_id
        )
        return msg

    async def _remove_wait_phrase(self, tmp_msg: TmpMessage):
        await self._bot.delete_message(self._chat_id, tmp_msg.wait_phrase_msg)
        await self._bot.delete_message(self._chat_id, tmp_msg.hourglass_msg)

    async def start_story(self, start_prompt: str, context_prompt):
        self._story_id = await self._user.stories.create(context_prompt)
        return await self.iter_story(start_prompt)

    def _select_wait_phrase(self) -> str:
        return "🤖 " + random.choice(self._wait_phrases)

    async def _preload_option(self, option: str) -> tuple[str, list[str], str]:
        logger.debug("Start preload: {}", option)
        text, options = await self._story.load_story(option)
        logger.debug("Preload option text: {} done", option)
        img_desc = await self._openai_api.get_completion(
            [{"role": "user",
              "content": f"Write a short prompt in English to generate "
                         f"an image with DALLE to illustrate this story: \"{text}\". "
                         f"Write only prompt, nothing more"}])
        logger.debug("Img prompt done: {}", img_desc)
        img = await self._openai_api.get_img(img_desc)
        logger.debug("Preload option image: {} done", option)
        await self._get_img_content(img)
        logger.debug("Image downloaded: {}", option)
        return text, options, img

    async def _wait_option_preload(self, option: str):
        img = None
        for opt, task in self._load_tasks:
            if opt != option:
                task.cancel()
                logger.debug("Cancel task for option: {}", option)
        for opt, task in self._load_tasks:
            if opt == option:
                _, _, img = await task
        self._load_tasks = []
        return img

    async def _get_story(self, option: str) -> tuple[str, list[str], str]:
        img = await self._wait_option_preload(option)
        text, options = await self._story.get_story(option)
        self._current_options = options

        if img is None:
            img = await self._openai_api.get_img(text)

        for option in options:
            task = asyncio.create_task(self._preload_option(option))
            self._load_tasks.append((option, task))
        return text, options, img

    @classmethod
    def _build_message(cls, text: str, options: list[str]) -> tuple[str, list[str]]:
        if len(options) == 0:
            return text, []
        message = f"{text}\n\nВыберите вариант:"
        btns = []

        for i, option in enumerate(options):
            message += f"\n\n{i + 1}. {option}"
            btns.append(f"{i + 1}")
        return message.strip(), btns

    async def _get_img_content(self, img: str) -> bytes:
        if img not in self._img_content:
            async with aiohttp.ClientSession() as session:
                async with session.get(img) as response:
                    self._img_content[img] = await response.read()
        return self._img_content[img]

    async def iter_story(self, option: str):
        if option.isnumeric() and self._story_id is None:
            raise ValueError("Story not started")
        if option.isnumeric() and self._current_options:
            await self._user.stories.update_option(self._story_item_id, int(option))
            option = self._current_options[int(option) - 1]

        wait_msg = await self._send_wait_phrase()

        text, options, img = await self._get_story(option)
        message, btns = self._build_message(text, options)
        self._story_item_id = await self._user.stories.add_text(self._story_id, message, img)

        if len(message) > 1020:
            logger.warning("Message too long: {}", self._story_item_id)
            message = message[:1020] + "..."

        await self._remove_wait_phrase(wait_msg)
        await self._bot.send_chat_action(chat_id=self._chat_id, action="typing")

        keyboard = []
        if btns:
            keyboard.append(btns)
        keyboard.append([buttons["restart"]])

        img_file = InputFile(io.BytesIO(await self._get_img_content(img)))
        await self._bot.send_photo(
            chat_id=self._chat_id, photo=img_file, caption=message,
            reply_markup=gen_keyboard(keyboard)
        )
