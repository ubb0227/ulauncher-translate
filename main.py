from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.CopyToClipboardAction import CopyToClipboardAction
from ulauncher.api.shared.action.HideWindowAction import HideWindowAction
import requests

API_KEY = "b0199911-c12d-4e91-8bdc-bf85e9ed4d23:fx"
API_URL = "https://api-free.deepl.com/v2/translate"
USAGE_URL = "https://api-free.deepl.com/v2/usage"

def get_usage_stats():
    """取得 DeepL 字數使用量"""
    try:
        res = requests.post(USAGE_URL, data={"auth_key": API_KEY})
        res.raise_for_status()
        data = res.json()
        used = data.get("character_count", 0)
        total = data.get("character_limit", 500000)
        return f"已用 {used:,}/{total:,} 字 (剩餘 {total - used:,})"
    except Exception:
        return "字數統計暫不可用"

def translate_with_alternatives(text, to_lang="ZH", from_lang="EN"):
    """取得翻譯結果與替代方案"""
    try:
        # 第一次翻譯 (主要結果)
        params = {
            "auth_key": API_KEY,
            "text": text,
            "target_lang": to_lang.upper(),
            "split_sentences": "0"  # 禁用句子分割以獲得更一致結果
        }
        res = requests.post(API_URL, data=params).json()
        main_translation = res["translations"][0]["text"]

        # 第二次翻譯 (強制不同結果)
        params["tag_handling"] = "html"  # 觸發不同處理方式
        alt_res = requests.post(API_URL, data=params).json()
        alt_translation = alt_res["translations"][0]["text"]

        # 第三次翻譯 (使用不同參數)
        params["preserve_formatting"] = "1"
        alt_res2 = requests.post(API_URL, data=params).json()
        alt_translation2 = alt_res2["translations"][0]["text"]

        # 移除重複項
        translations = list({main_translation, alt_translation, alt_translation2})
        
        return translations
    except Exception as e:
        return [f"翻譯錯誤: {str(e)}"]

class DeeplTranslator(Extension):
    def __init__(self):
        super().__init__()
        self.subscribe(KeywordQueryEvent, self.TranslateHandler())

    class TranslateHandler(EventListener):
        def on_event(self, event, extension):
            query = event.get_argument() or ""
            default_to = extension.preferences.get("mainlang", "ZH")
            default_from = extension.preferences.get("otherlang", "EN")

            if not query.strip():
                return RenderResultListAction([
                    ExtensionResultItem(
                        icon="images/icon.png",
                        name="輸入要翻譯的文字",
                        description=f"當前字數狀態: {get_usage_stats()}",
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

            translations = translate_with_alternatives(text, to_lang, from_lang)
            usage = get_usage_stats()

            # 構建多結果列表
            items = []
            for i, trans in enumerate(translations):
                items.append(
                    ExtensionResultItem(
                        icon="images/icon.png",
                        name=trans,
                        description=f"{i+1}/{len(translations)} | {from_lang or 'auto'} => {to_lang}",
                        on_enter=CopyToClipboardAction(trans),
                        highlightable=True
                    )
                )

            # 在最上方添加使用量資訊
            items.insert(0, ExtensionResultItem(
                icon="images/icon.png",
                name=f"「{text}」的翻譯結果",
                description=usage,
                on_enter=HideWindowAction()
            ))

            return RenderResultListAction(items)

if __name__ == "__main__":
    DeeplTranslator().run()
