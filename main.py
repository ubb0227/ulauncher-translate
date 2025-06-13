from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.CopyToClipboardAction import CopyToClipboardAction
from ulauncher.api.shared.action.HideWindowAction import HideWindowAction
import requests
from threading import Thread
from functools import lru_cache

API_KEY = "b0199911-c12d-4e91-8bdc-bf85e9ed4d23:fx"
API_URL = "https://api-free.deepl.com/v2/translate"
USAGE_URL = "https://api-free.deepl.com/v2/usage"

@lru_cache(maxsize=100)
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

class DeeplTranslator(Extension):
    def __init__(self):
        super().__init__()
        self.session = requests.Session()
        # 預熱連接
        try:
            self.session.get("https://api-free.deepl.com", timeout=2)
        except:
            pass
        self.subscribe(KeywordQueryEvent, self.TranslateHandler())

    class TranslateHandler(EventListener):
        def on_event(self, event, extension):
            query = event.get_argument() or ""
            default_to = extension.preferences.get("mainlang", "EN")
            default_from = extension.preferences.get("otherlang", "")

            if not query.strip():
                return RenderResultListAction([
                    ExtensionResultItem(
                        icon="images/icon.png",
                        name="輸入要翻譯的文字",
                        description="按Enter開始翻譯",
                        on_enter=HideWindowAction()
                    )
                ])

            parts = query.split(maxsplit=1)
            if len(parts) > 1 and ":" in parts[0]:
                from_lang, to_lang = parts[0].split(":", 1)
                text = parts[1]
            else:
                from_lang, to_lang = default_from, default_to
                text = query

            # 創建初始結果
            result = [ExtensionResultItem(
                icon="images/icon.png",
                name="翻譯中...",
                description="請稍候",
                on_enter=HideWindowAction(),
                highlightable=False
            )]
            
            # 啟動異步翻譯
            Thread(target=self._async_translate, 
                 args=(extension, text, to_lang, from_lang, result)).start()
            
            return RenderResultListAction(result)
        
        def _async_translate(self, extension, text, to_lang, from_lang, result):
            translated = translate(text, to_lang, from_lang)
            usage = get_usage_stats()
            
            result[0] = ExtensionResultItem(
                icon="images/icon.png",
                name=f"{translated}",
                description=f"{usage} | {from_lang or 'auto'} ==> {to_lang}",
                on_enter=CopyToClipboardAction(translated),
                highlightable=False
            )

if __name__ == "__main__":
    DeeplTranslator().run()
