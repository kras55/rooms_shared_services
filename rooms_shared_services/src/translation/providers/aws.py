import boto3
from mypy_boto3_translate import TranslateClient

from rooms_shared_services.src.models.texts.languages import Language
from rooms_shared_services.src.translation.providers.abstract import AbstractTranslationProvider

client: TranslateClient = boto3.client("translate")


class AWSTranslationProvider(AbstractTranslationProvider):
    def translate(self, txt: str, source: Language, target: Language):
        return client.translate_text(Text=txt, SourceLanguageCode=source.name, TargetLanguageCode=target.name)
