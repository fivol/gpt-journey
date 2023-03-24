import openai
from loguru import logger


class OpenAIAPI:
    def __init__(self, token: str):
        openai.api_key = token

    @classmethod
    def get_img(cls, prompt, size: str = "256x256") -> str:
        try:
            response = openai.Image.create(
                prompt=prompt,
                n=1,
                size=size
            )
            img_url = response.data[0].url
        except:
            logger.exception("OpenAI API error")
            img_url = "https://pythonprogramming.net/static/images/imgfailure.png"
        return img_url

    @classmethod
    def get_completion(cls, message_history: list[dict[str, str]]) -> str:
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=message_history
        )
        return completion.choices[0].message.content
