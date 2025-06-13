from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.CopyToClipboardAction import CopyToClipboardAction
from ulauncher.api.shared.action.HideWindowAction import HideWindowAction
import requests

API_KEY = "b0199911-c12d-4e91-8bdc-bf85e9ed4d23:fx"  # 建議移至環境變數
API_URL = "https://api-free.deepl.com/v2/translate"
USAGE_URL = "https://api-free.deepl.com/v2/usage"

def get_usage_stats():
    """取得 DeepL 字數使用量 (簡潔版)"""
    try:
        res = requests.post(USAGE_URL, data={"auth_key": API_KEY})
        res.raise_for_status()
        data = res.json()
        used = data.get("character_count", 0)
        total = data.get("character_limit", 500000)
        return f"已用 {used:,}/{total:,} 字 (剩餘 {total - used:,})"
    except Exception:
        return "字數統計暫不可用"

def translate(text, to_lang="EN", from_lang=None):
    """只返回翻譯結果"""
    params = {
        "auth_key": API_KEY,
        "text": text,
        "target_lang": to_lang.upper().replace("AUTO", "")
    }
    if from_lang and from_lang.upper() not in ("", "AUTO"):
        params["source_lang"] = from_lang.upper()

    try:
        res = requests.post(API_URL, data=params)
        res.raise_for_status()
        return res.json()["translations"][0]["text"]
    except Exception as e:
        return f"翻譯錯誤: {str(e)}"

class DeeplTranslator(Extension):
    def __init__(self):
        super().__init__()
        self.subscribe(KeywordQueryEvent, self.TranslateHandler())

    class TranslateHandler(EventListener):
        def on_event(self, event, extension):
            query = event.get_argument() or ""
            default_to = extension.preferences.get("mainlang", "EN")
            default_from = extension.preferences.get("otherlang", "")

            # 空輸入時顯示提示
            if not query.strip():
                return RenderResultListAction([
                    ExtensionResultItem(
                        icon="images/icon.png",
                        name="輸入要翻譯的文字 (例: zh:en 你好)",
                        description=f"當前字數狀態: {get_usage_stats()}",
                        on_enter=HideWindowAction()
                    )
                ])

            # 解析語言代碼
            parts = query.split(maxsplit=1)
            if len(parts) > 1 and ":" in parts[0]:
                from_lang, to_lang = parts[0].split(":", 1)
                text = parts[1]
            else:
                from_lang, to_lang = default_from, default_to
                text = query

            # 獲取結果
            translated = translate(text, to_lang, from_lang)
            usage = get_usage_stats()

            return RenderResultListAction([
                ExtensionResultItem(
                    icon="images/icon.png",
                    name=f"{translated}",
                    description=f"{usage} | {from_lang or 'auto'} -> {to_lang}",
                    on_enter=CopyToClipboardAction(translated),
                    highlightable=False
                )
            ])

if __name__ == "__main__":
    DeeplTranslator().run()
