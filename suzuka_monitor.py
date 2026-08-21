import time
import requests
from playwright.sync_api import sync_playwright

BOT_TOKEN = "8935836445:AAHt6Ko-8TZS-Z7gli7TMpm-KzFlr1JzFG8"
CHAT_ID = "118523258"
TARGET_URL = "https://www.asoview.com/item/ticket/ticket0000007351/"

# 監控目標日期：9月4日 及 9月7日
TARGET_DAYS = ["4", "7"]

def send_telegram_alert(message):
    api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        requests.post(api_url, json=payload, timeout=10)
        print("Telegram 通知已發送！")
    except Exception as e:
        print(f"發送通知失敗: {e}")

def check_ticket():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 900}
        )
        page = context.new_page()

        try:
            print("1. 打開商品主頁...")
            page.goto(TARGET_URL, timeout=45000, wait_until="domcontentloaded")
            time.sleep(2.5)

            # 2. 點擊進入購票頁面
            buy_btn = page.locator('text="購入に進む"')
            if buy_btn.count() > 0 and buy_btn.first.is_visible():
                buy_btn.first.click()
                time.sleep(3)

            # 3. 處理「同意」彈窗
            agree_btn = page.locator('button:has-text("同意します"), button:has-text("同意")')
            if agree_btn.count() > 0 and agree_btn.first.is_visible():
                agree_btn.first.click()
                time.sleep(2.5)

            # 4. DOM 精確檢查
            result_status = page.evaluate('''(targetDays) => {
                const results = {};
                const dateSpans = Array.from(document.querySelectorAll('[class*="dateValue"]'));

                targetDays.forEach(day => {
                    const matched = dateSpans.filter(el => el.innerText && el.innerText.trim() === String(day));
                    if (matched.length === 0) {
                        results[day] = { found: false, isSoldOut: true };
                        return;
                    }

                    const septDateSpan = matched[matched.length - 1];
                    const tdCell = septDateSpan.closest('td');
                    if (!tdCell) {
                        results[day] = { found: false, isSoldOut: true };
                        return;
                    }

                    const hasDisabledClass = /Disabled/i.test(tdCell.className || '');
                    const hasSvgIcon = tdCell.querySelector('svg') !== null;
                    results[day] = {
                        found: true,
                        isSoldOut: hasDisabledClass || hasSvgIcon
                    };
                });
                return results;
            }''', TARGET_DAYS)

            available_days = []
            for day in TARGET_DAYS:
                info = result_status.get(day, {})
                if info.get('found') and not info.get('isSoldOut', True):
                    available_days.append(day)

            if available_days:
                days_str = "、".join([f"9月{d}日" for d in available_days])
                msg = f"🚨 <b>【鈴鹿賽道挑戰者】有飛釋出！</b>\n\n🎯 <b>釋出日期：{days_str}</b>\n\n🔗 即刻點擊搶購：\n{TARGET_URL}"
                send_telegram_alert(msg)
                print(f"發現名額釋出：{days_str}")
            else:
                print("檢查完成：9月4日 及 9月7日 均無票。")

        except Exception as e:
            print(f"執行出錯: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    check_ticket()
