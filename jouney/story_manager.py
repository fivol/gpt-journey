import asyncio
import re

from loguru import logger

from jouney.api_provider import OpenAIAPI


class StoryManager:
    def __init__(self, story_prompt: str, assistant_answer: str, openai_api: OpenAIAPI):
        self._message_history = self._get_init_messages(story_prompt, assistant_answer)
        self._openai_api = openai_api
        self._cache = {}

    def _clear_cache(self):
        self._cache = {}

    def set_context(self, text: str):
        self._message_history.append({
            "role": "user",
            "content": f"The setting of the story is as follows: {text}"
        })

    @classmethod
    def _get_init_messages(cls, story_prompt: str, assistant_answer: str) -> list[dict]:
        return [
            {"role": "user", "content": story_prompt},
            {"role": "assistant", "content": assistant_answer}
        ]

    async def load_story(self, option: str):
        history_copy = self._message_history.copy()
        history_copy = self._add_option(history_copy, option)
        reply_content = await self._chat(history_copy)
        self._cache[option] = reply_content
        return self._split_story(reply_content)

    @classmethod
    def _split_story(cls, reply_content: str) -> tuple[str, list[str]]:
        text = reply_content.split("1: ")[0].strip()
        options = re.findall(r"\d: (.*)", reply_content)
        options = [item.strip() for item in options]
        return text, options

    async def get_story(self, option: str) -> tuple[str, list[str]]:
        self._select_option(option)
        if option in self._cache:
            logger.debug("Get story from cache")
            reply_content = self._cache[option]
        else:
            reply_content = await self._chat(self._message_history)

        self._add_completion(reply_content)
        self._clear_cache()
        logger.debug("Story generated")

        print(reply_content)
        print("\n\n")

        return self._split_story(reply_content)

    @classmethod
    def _add_option(cls, history, option: str) -> list[dict]:
        history.append({
            "role": "user",
            "content": option
        })
        return history

    def _add_completion(self, reply_content: str):
        self._message_history.append({"role": "assistant", "content": f"{reply_content}"})

    def _select_option(self, option: str):
        self._message_history = self._add_option(self._message_history, option)

    async def _chat(self, message_history) -> str:
        return await self._openai_api.get_completion(message_history)
