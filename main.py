from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.CopyToClipboardAction import CopyToClipboardAction
from ulauncher.api.shared.action.HideWindowAction import HideWindowAction

import requests
import textwrap


def translate(text, target_lang="EN", source_lang="AUTO", wrap_len="80"):
    api_key = "b0199911-c12d-4e91-8bdc-bf85e9ed4d23:fx"
    url = "https://api-free.deepl.com/v2/translate"
    try:
        response = requests.post(
            url,
            data={
                "auth_key": api_key,
                "text": text,
                "source_lang": source_lang.upper(),
                "target_lang": target_lang.upper()
            }
        )
        response.raise_for_status()
        result = response.json()
        translated_text = result["translations"][0]["text"]
        return "\n".join(textwrap.wrap(translated_text, int(wrap_len)))
    except Exception as e:
        return f"翻譯錯誤：{e}"


class TranslateExtension(Extension):
    def __init__(self):
        super().__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())


class KeywordQueryEventListener(EventListener):
    def on_event(self, event, extension):
        query = event.get_argument() or ""
        preferences = extension.preferences

        # 取得設定參數
        wrap_len = preferences.get("wrap", "80")
        default_source = preferences.get("otherlang", "AUTO")
        default_target = preferences.get("mainlang", "EN")

        query = query.strip()

        if not query:
            return RenderResultListAction([
                ExtensionResultItem(
                    icon='images/icon.png',
                    name='請輸入要翻譯的文字',
                    on_enter=HideWindowAction()
                )
            ])

        # 支援 zh:en 這種格式切換語言
        if len(query) > 5 and query[2] == ":":
            source_lang = query[:2]
            target_lang = query[3:5]
            text = query[5:].strip()
        else:
            source_lang = default_source
            target_lang = default_target
            text = query

        translated = translate(text, target_lang, source_lang, wrap_len)

        return RenderResultListAction([
            ExtensionResultItem(
                icon='images/icon.png',
                name=text,
                description=translated,
                on_enter=CopyToClipboardAction(translated)
            )
        ])


if __name__ == "__main__":
    TranslateExtension().run()
