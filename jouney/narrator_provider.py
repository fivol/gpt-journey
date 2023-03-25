from jouney.api_provider import OpenAIAPI
from jouney.data import DataProvider
from jouney.narrator import Narrator
from jouney.story_manager import StoryManager
from jouney.user import UserDB


class NarratorProvider:
    def __init__(self, bot, openai_api: OpenAIAPI, wait_phrases: list[str] = None):
        self._bot = bot
        self._openai_api = openai_api
        self._wait_phrases = wait_phrases

        self._narrators = {}

    def create_narrator(self, chat_id: int, story: StoryManager, user: UserDB, data: DataProvider) -> Narrator:
        narrator = Narrator(self._bot, chat_id, story, self._openai_api, user, data)
        self._narrators[chat_id] = narrator
        return narrator

    def get_narrator(self, chat_id: int) -> Narrator | None:
        return self._narrators.get(chat_id)

    def remove_narrator(self, chat_id: int):
        self._narrators.pop(chat_id, None)

