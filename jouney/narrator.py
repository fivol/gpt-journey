from aiogram.types import InputFile, KeyboardButton, ReplyKeyboardMarkup

from jouney.api_provider import OpenAIAPI
from jouney.data import buttons
from jouney.story_manager import StoryManager


class Narrator:
    def __init__(self, bot, chat_id: int, story: StoryManager, openai_api: OpenAIAPI):
        self._chat_id = chat_id
        self._bot = bot
        self._story = story
        self._openai_api = openai_api

    async def start_story(self, message: str):
        return await self.iter_story(message)

    async def iter_story(self, option: str):
        """Show user typing telegram animation"""
        hourglass = await self._bot.send_message(self._chat_id, "⏳")
        await self._bot.send_chat_action(chat_id=self._chat_id, action="typing")
        text, options = self._story.get_story(option)
        img = self._openai_api.get_img(text)

        img_file = InputFile.from_url(img)

        message = f"{text}\n\nВыберите вариант:"
        btns = []

        for i, option in enumerate(options):
            message += f"\n\n{i + 1}. {option}"
            btns.append(KeyboardButton(f"{i + 1}"))

        await self._bot.delete_message(self._chat_id, hourglass.message_id)
        await self._bot.send_chat_action(chat_id=self._chat_id, action="typing")

        await self._bot.send_photo(chat_id=self._chat_id, photo=img_file, caption=message,
                                   reply_markup=ReplyKeyboardMarkup(
                                       [btns, [KeyboardButton(buttons["restart"])]],
                                       resize_keyboard=True))
