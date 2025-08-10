import os
import re
import requests
from playwright.sync_api import sync_playwright

# ===== 配置 =====
GTX_COOKIE = os.getenv("GTX_COOKIE")  # GitHub Secrets
SERVER_IDS = os.getenv("SERVER_IDS")  # 多个服务器 ID 用逗号分隔
TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN")  # Telegram Bot Token
TG_CHAT_ID = os.getenv("TG_CHAT_ID")  # Telegram Chat ID

if not GTX_COOKIE or not SERVER_IDS or not TG_BOT_TOKEN or not TG_CHAT_ID:
    raise ValueError("请设置 GTX_COOKIE, SERVER_IDS, TG_BOT_TOKEN, TG_CHAT_ID 环境变量")

SERVER_IDS = [sid.strip() for sid in SERVER_IDS.split(",")]

# 发送 Telegram 消息
def send_tg(msg):
    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TG_CHAT_ID, "text": msg, "parse_mode": "HTML"}
    try:
        requests.post(url, data=data, timeout=10)
    except Exception as e:
        print(f"Telegram 发送失败: {e}")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context()

    # 设置 Cookie
    context.add_cookies([
        {
            "name": c.split("=")[0].strip(),
            "value": "=".join(c.split("=")[1:]).strip(),
            "domain": "gamepanel2.gtxgaming.co.uk",
            "path": "/",
            "httpOnly": False,
            "secure": True
        }
        for c in GTX_COOKIE.split("; ")
    ])

    page = context.new_page()

    for sid in SERVER_IDS:
        url = f"https://gamepanel2.gtxgaming.co.uk/server/{sid}"
        print(f"➡ 正在访问服务器 {sid} ...")
        page.goto(url)

        # 检查是否登录成功
        if "login" in page.url.lower():
            send_tg(f"⚠ 服务器 {sid} 登录失败，Cookie 可能已失效")
            continue

        # 获取原到期时间
        try:
            expiry_text = page.locator("text=EXPIRY DATE").locator("xpath=..").inner_text()
            old_date_match = re.search(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", expiry_text)
            old_date = old_date_match.group(0) if old_date_match else None
        except:
            old_date = None

        # 点击 EXTEND 按钮
        try:
            page.wait_for_selector("text=EXTEND 72 HOUR(S)", timeout=10000)
            page.click("text=EXTEND 72 HOUR(S)")
            page.wait_for_timeout(2000)  # 等待弹窗出现
        except:
            send_tg(f"⚠ 服务器 {sid} 找不到续期按钮")
            continue

        # 检查是否出现“已续期”提示
        if "already extended" in page.content().lower():
            send_tg(f"ℹ 服务器 {sid} 今日已续期，无法重复")
            continue

        # 检查是否续期成功（对比到期时间）
        try:
            page.reload()
            expiry_text_new = page.locator("text=EXPIRY DATE").locator("xpath=..").inner_text()
            new_date_match = re.search(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", expiry_text_new)
            new_date = new_date_match.group(0) if new_date_match else None
        except:
            new_date = None

        if new_date and old_date and new_date != old_date:
            send_tg(f"✅ 服务器 {sid} 续期成功\n旧到期时间: {old_date}\n新到期时间: {new_date}")
        else:
            send_tg(f"⚠ 服务器 {sid} 点击了续期按钮，但到期时间无变化")

    browser.close()
