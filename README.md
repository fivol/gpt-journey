# gpt-journey

A Telegram bot that runs a text adventure written on the fly by GPT. It
describes a situation, offers 2–4 options as inline buttons, and continues the
story from whichever one you pick — indefinitely, in Russian or English.

Inspired by [GPT-Journey by Sentdex](https://github.com/Sentdex/GPT-Journey).

## How it works

```
handlers.py        # Telegram commands and button callbacks
story_manager.py   # keeps the story going: state, choices, continuation
narrator.py        # turns model output into a scene + options
narrator_provider.py / api_provider.py   # OpenAI calls, retries, model config
data.py            # prompts, texts and buttons, per language
db.py models.py    # PostgreSQL: users, stories, progress
```

The prompt that defines the game, the interface strings and the buttons all
live in `data/*.json` (`prompts.json`, `texts.json`, `buttons.json` and their
`_en` counterparts), so changing the game or adding a language never touches
Python.

## Run it

```bash
cp .env.example .env      # fill in BOT_TOKEN and OPENAI_API_KEY
pip install -r requirements.txt
python main.py
```

With Docker (brings up PostgreSQL too):

```bash
cp .env.example .env
docker compose up -d --build
```

## Configuration

Configuration is read with [bestconfig](https://github.com/fivol/bestconfig),
so every key below works as an environment variable, a line in `.env`, or an
entry in `config.yml`.

| Variable | Required | What it is |
|---|---|---|
| `BOT_TOKEN` | yes | Telegram bot token from [@BotFather](https://t.me/BotFather) |
| `OPENAI_API_KEY` | yes | OpenAI API key |
| `PG_URL` | yes | `postgresql://user:pass@host:5432/db` |
| `PG_PORT` | no | Host port for the bundled PostgreSQL (Docker only) |

## License

MIT — see [LICENSE](LICENSE).
