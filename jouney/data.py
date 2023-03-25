import os.path

from jouney.accessor import FileAccessor


class CompositeFileAccessor(FileAccessor):
    def __init__(self, *accessors: FileAccessor):  # noqa
        self._accessors = accessors

    def get(self, key: str) -> str:
        for accessor in self._accessors:
            try:
                return accessor.get(key)
            except KeyError:
                pass
        raise KeyError(key)


class DataProvider:
    accessors = {}

    @classmethod
    def _get_file_path(cls, name: str, lang: str | None = None) -> str:
        if lang is not None:
            return f"data/{name}_{lang}.json"
        return f"data/{name}.json"

    @classmethod
    def _get_accessor(cls, name: str, lang: str | None = None) -> FileAccessor:
        path = cls._get_file_path(name, lang)
        if (name, lang) not in cls.accessors:
            cls.accessors[(name, lang)] = FileAccessor(path)
        return cls.accessors[(name, lang)]

    def __init__(self, lang: str):
        self._lang = lang
        self.buttons = self._get_composite_accessor("buttons")
        self.texts = self._get_composite_accessor("texts")
        self.prompts = self._get_composite_accessor("prompts")

    def _get_composite_accessor(self, name: str) -> FileAccessor:
        accessors = []
        if os.path.exists(self._get_file_path(name, self._lang)):
            accessors.append(self._get_accessor(name, self._lang))
        if os.path.exists(self._get_file_path(name)):
            accessors.append(self._get_accessor(name))

        if len(accessors) == 1:
            return accessors[0]
        return CompositeFileAccessor(*accessors)


data_ru = DataProvider("ru")
data_en = DataProvider("en")


class States:
    wait_story_desc = "wait_story_desc"
    story = "story"


