import re
from jouney.api_provider import OpenAIAPI


class StoryManager:
    def __init__(self, story_prompt: str, assistant_answer: str, openai_api: OpenAIAPI):
        self._message_history = self._get_init_messages(story_prompt, assistant_answer)
        self._openai_api = openai_api

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

    def get_story(self, option: str) -> tuple[str, list[str]]:
        reply_content, message_history = self._chat(option)

        print(reply_content)
        print("\n\n\n\n")

        text = reply_content.split("1: ")[0].strip()

        options = re.findall(r"\d: (.*)", reply_content)

        return text, options

    def _chat(self, message):
        message_history = self._message_history
        message_history.append({"role": "user", "content": message})

        reply_content = self._openai_api.get_completion(message_history)

        message_history.append({"role": "assistant", "content": f"{reply_content}"})

        return reply_content, message_history
