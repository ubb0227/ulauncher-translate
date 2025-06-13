from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.CopyToClipboardAction import CopyToClipboardAction
from ulauncher.api.shared.action.HideWindowAction import HideWindowAction

import requests
import textwrap


DEEPL_LANGUAGES = {
    "zh": "ZH",
    "en": "EN",
    "en-us": "EN-US",
    "en-gb": "EN-GB",
    "ja": "JA",
    "ko": "KO",
    "fr": "FR",
    "de": "DE",
    "es": "ES",
    "it": "IT",
    "nl": "NL",
    "pl": "PL",
    "pt": "PT-PT",
    "pt-br": "PT-BR",
    "ru": "RU",
    "auto": "AUTO"
}


def normalize_lang(code):
    return DEEPL_LANGUAGES.get(code.lower(), code.upper())


def translate(text, to_language="EN", from_language="AUTO", wrap_len="80"):
    api_key = "b0199911-c12d-4e91-8bdc-bf85e9ed4d23:fx"
    url = "https://api-free.deepl.com/v2/translate"
    try:
        response = requests.post(
            url,
            data={
                "auth_key": api_key,
                "text": text,
                "source_lang": normalize_lang(from_language),
                "target_lang": normalize_lang(to_language)
            }
        )
        response.raise_for_status()
        result = response.json()
        translated_text = result["translations"][0]["text"]
        return "\n".join(textwrap.wrap(translated_text, int(wrap_len) if wrap_len.isdigit() else 80))
    except Exception as e:
        return f"翻譯錯誤：{e}"


class TranslateExtension(Extension):
    def __init__(self):
        super(TranslateExtension, self).__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())


class KeywordQueryEventListener(EventListener):
    def on_event(self, event, extension):
        query = event.get_argument() or ""
        wrap = extension.preferences.get("wrap", "80")
        default_from = extension.preferences.get("otherlang", "AUTO")
        default_to = extension.preferences.get("mainlang", "EN")

        query = query.strip()

        if not query:
            return RenderResultListAction([
                ExtensionResultItem(
                    icon='images/icon.png',
                    name='請輸入要翻譯的文字',
                    on_enter=HideWindowAction()
                )
            ])

        # 語言代碼格式為: zh:en 你好
        if len(query) > 5 and query[2] == ":":
            from_lang = query[:2]
            to_lang = query[3:5]
            text = query[5:].strip()
        else:
            from_lang = default_from
            to_lang = default_to
            text = query

        translated = translate(text, to_lang, from_lang, wrap)

        return RenderResultListAction([
            ExtensionResultItem(
                icon='images/icon.png',
                name=f"{text}",
                description=translated,
                on_enter=CopyToClipboardAction(translated)
            )
        ])


if __name__ == '__main__':
    TranslateExtension().run()
