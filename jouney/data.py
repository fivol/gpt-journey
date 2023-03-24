from jouney.accessor import FileAccessor

prompts = FileAccessor("data/prompts.json")
buttons = FileAccessor("data/buttons.json")
texts = FileAccessor("data/texts.json")


class States:
    wait_story_desc = "wait_story_desc"
    story = "story"
