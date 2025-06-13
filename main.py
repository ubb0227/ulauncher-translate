from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.CopyToClipboardAction import CopyToClipboardAction
from ulauncher.api.shared.action.HideWindowAction import HideWindowAction

import requests
import textwrap

API_KEY = "b0199911-c12d-4e91-8bdc-bf85e9ed4d23:fx"
API_URL = "https://api-free.deepl.com/v2/translate"
USAGE_URL = "https://api-free.deepl.com/v2/usage"

def normalize_lang(lang_code):
    """轉換為 DeepL 認可的語言代碼"""
    return lang_code.strip().upper().replace("AUTO", "")

def get_usage_stats():
    """查詢 DeepL API 使用量統計"""
    try:
        response = requests.post(USAGE_URL, data={"auth_key": API_KEY})
        response.raise_for_status()
        usage_data = response.json()
        return (
            f"{usage_data.get('character_count', 0):,}/{usage_data.get('character_limit', 500000):,} "
            f"(剩餘 {usage_data.get('character_limit', 0) - usage_data.get('character_count', 0):,})"
        )
    except Exception as e:
        return f"使用量查詢失敗: {str(e)}"

def translate(text, to_language="EN", from_language=None, wrap_len="80"):
    data = {
        "auth_key": API_KEY,
        "text": text,
        "target_lang": normalize_lang(to_language)
    }

    if from_language and normalize_lang(from_language):
        data["source_lang"] = normalize_lang(from_language)

    try:
        response = requests.post(API_URL, data=data)
        response.raise_for_status()
        result = response.json()
        translated_text = result["translations"][0]["text"]
        
        # 加大字體顯示的格式化
        formatted_text = f"<big><b>原始文字:</b></big>\n{text}\n\n<big><b>翻譯結果:</b></big>\n{translated_text}"
        wrapped_text = "\n".join(textwrap.wrap(formatted_text, int(wrap_len) if wrap_len.isdigit() else 80))
        return wrapped_text
    except Exception as e:
        return f"<big>翻譯錯誤：{e}</big>"

class TranslateExtension(Extension):
    def __init__(self):
        super(TranslateExtension, self).__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())

class KeywordQueryEventListener(EventListener):
    def on_event(self, event, extension):
        query = event.get_argument() or ""
        wrap = extension.preferences.get("wrap", "80")
        default_from = extension.preferences.get("otherlang", "")
        default_to = extension.preferences.get("mainlang", "EN")

        # 獲取使用量資訊
        usage_stats = get_usage_stats()

        query = query.strip()
        if not query:
            return RenderResultListAction([
                ExtensionResultItem(
                    icon='images/icon.png',
                    name='請輸入要翻譯的文字',
                    description=f"DeepL 使用量: {usage_stats}",
                    on_enter=HideWindowAction()
                )
            ])

        # 語言格式判斷：zh:en text
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
                name=f"翻譯結果 (使用量: {usage_stats})",
                description=translated,
                on_enter=CopyToClipboardAction(
                    translated.replace("<big>", "")
                    .replace("</big>", "")
                    .replace("<b>", "")
                    .replace("</b>", "")
                ),
                highlightable=False
            )
        ])

if __name__ == '__main__':
    TranslateExtension().run()
