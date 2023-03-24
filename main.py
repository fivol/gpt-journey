from aiogram.utils import executor

from jouney.bot import dp
import jouney.handlers  # noqa

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
