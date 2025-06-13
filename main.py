#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from threading import Thread
import logging
from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.HideWindowAction import HideWindowAction
from ulauncher.api.shared.action.CopyToClipboardAction import CopyToClipboardAction
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem

# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# DeepL API 配置
API_KEY = "b0199911-c12d-4e91-8bdc-bf85e9ed4d23:fx"  # 替換為你的實際API密鑰
API_URL = "https://api-free.deepl.com/v2/translate"
USAGE_URL = "https://api-free.deepl.com/v2/usage"

def translate(text, to_lang="EN", from_lang=""):
    """
    使用DeepL API翻譯文本
    :param text: 要翻譯的文本
    :param to_lang: 目標語言代碼 (預設: EN)
    :param from_lang: 源語言代碼 (可選)
    :return: 翻譯結果或錯誤訊息
    """
    params = {
        "auth_key": API_KEY,
        "text": text,
        "target_lang": to_lang.upper(),
        "source_lang": from_lang.upper() if from_lang else None
    }
    
    try:
        logger.debug(f"正在翻譯: {text} (從 {from_lang} 到 {to_lang})")
        res = requests.post(API_URL, data=params, timeout=10)
        res.raise_for_status()
        
        # 檢查響應數據
        if not res.json().get("translations"):
            raise ValueError("API響應中沒有翻譯結果")
            
        return res.json()["translations"][0]["text"]
    except requests.exceptions.RequestException as e:
        logger.error(f"API請求失敗: {str(e)}")
        return f"翻譯錯誤: 網路請求失敗 ({str(e)})"
    except Exception as e:
        logger.error(f"翻譯過程中出錯: {str(e)}")
        return f"翻譯錯誤: {str(e)}"

def get_usage_stats():
    """獲取 DeepL 字數使用量統計"""
    try:
        res = requests.post(USAGE_URL, data={"auth_key": API_KEY}, timeout=5)
        res.raise_for_status()
        data = res.json()
        used = data.get("character_count", 0)
        total = data.get("character_limit", 500000)
        return f"已用 {used:,}/{total:,} 字 (剩餘 {total - used:,})"
    except Exception as e:
        logger.error(f"獲取使用統計失敗: {str(e)}")
        return "字數統計暫不可用"

class DeeplTranslator(Extension):
    def __init__(self):
        super().__init__()
        self.session = requests.Session()
        # 預熱連接
        try:
            self.session.get("https://api-free.deepl.com", timeout=2)
        except Exception as e:
            logger.warning(f"預熱連接失敗: {str(e)}")
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
                        on_enter=HideWindowAction()
                    )
                ])

            # 解析語言對 (格式: "from:to 文本" 或 "to 文本")
            parts = query.split(maxsplit=1)
            if len(parts) > 1 and ":" in parts[0]:
                lang_pair = parts[0].split(":", 1)
                from_lang = lang_pair[0].strip().upper()
                to_lang = lang_pair[1].strip().upper()
                text = parts[1]
            else:
                from_lang = default_from
                to_lang = default_to
                text = query

            # 創建初始結果
            result = [ExtensionResultItem(
                icon="images/icon.png",
                name="翻譯中...",
                on_enter=HideWindowAction(),
                highlightable=False
            )]
            
            # 啟動異步翻譯
            Thread(
                target=self._async_translate,
                args=(extension, text, to_lang, from_lang, result),
                daemon=True
            ).start()
            
            return RenderResultListAction(result)
        
        def _async_translate(self, extension, text, to_lang, from_lang, result):
            try:
                logger.info(f"開始翻譯: '{text}'")
                translated = translate(text, to_lang, from_lang)
                usage = get_usage_stats()
                
                # 更新結果
                result[0] = ExtensionResultItem(
                    icon="images/icon.png",
                    name=f"{translated}",
                    description=f"{usage} | {from_lang or 'auto'} → {to_lang}",
                    on_enter=CopyToClipboardAction(translated),
                    highlightable=False
                )
                logger.info(f"翻譯完成: '{text}' ==> '{translated}'")
            except Exception as e:
                logger.error(f"翻譯過程中出錯: {str(e)}")
                result[0] = ExtensionResultItem(
                    icon="images/icon.png",
                    name="翻譯失敗",
                    description=f"錯誤: {str(e)}",
                    highlightable=False
                )

if __name__ == "__main__":
    DeeplTranslator().run()
