from rooms_shared_services.src.models.texts.translations import Language, TextTranslations
from rooms_shared_services.src.translation.providers.abstract import AbstractTranslationProvider


class TranslationClient(object):
    def __init__(self, provider: AbstractTranslationProvider) -> None:
        """Set provider.

        Args:
            provider (AbstractTranslationProvider): _description_
        """
        self.provider = provider

    def bulk_translate(self, source_language: Language, target_languages: list[Language], txt: str) -> TextTranslations:
        translations = [
            self.provider.translate(txt=txt, source=source_language, target=target_language)
            for target_language in target_languages
        ]
        text_translations = TextTranslations(source=source_language)
        for target_language, translation in zip(target_languages, translations):
            setattr(text_translations, target_language.name, translation)
        return text_translations
