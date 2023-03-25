import openai
from loguru import logger


class OpenAIAPI:
    def __init__(self, token: str):
        openai.api_key = token

    @classmethod
    async def get_img(cls, prompt, size: str = "256x256") -> str:
        try:
            response = await openai.Image.acreate(
                prompt=prompt,
                n=1,
                size=size
            )
            img_url = response.data[0].url
        except openai.error.InvalidRequestError:
            logger.error("OpenAI Image safety error: {}", prompt.replace("\n", " "))
            img_url = "https://pythonprogramming.net/static/images/imgfailure.png"
        except:
            logger.exception("OpenAI API error")
            img_url = "https://pythonprogramming.net/static/images/imgfailure.png"
        return img_url

    @classmethod
    async def get_completion(cls, message_history: list[dict[str, str]]) -> str:
        completion = await openai.ChatCompletion.acreate(
            model="gpt-3.5-turbo",
            messages=message_history
        )
        return completion.choices[0].message.content
