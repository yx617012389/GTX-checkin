import os
from playwright.sync_api import sync_playwright

# 从环境变量读取 Cookie 和服务器 ID
GTX_COOKIE = os.getenv("GTX_COOKIE")  # 从 GitHub Secrets 中获取
SERVER_IDS = os.getenv("SERVER_IDS")  # 多个服务器 ID 用英文逗号分隔

if not GTX_COOKIE:
    raise ValueError("请设置 GTX_COOKIE 环境变量（在 GitHub Secrets 中）")
if not SERVER_IDS:
    raise ValueError("请设置 SERVER_IDS 环境变量（多个 ID 用逗号分隔）")

SERVER_IDS = [sid.strip() for sid in SERVER_IDS.split(",")]

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
        
        try:
            page.wait_for_selector("text=EXTEND 72 HOUR(S)", timeout=10000)
            page.click("text=EXTEND 72 HOUR(S)")
            print(f"✅ 服务器 {sid} 已点击 EXTEND 72 HOUR(S)")
        except Exception as e:
            print(f"⚠ 服务器 {sid} 续期失败：{e}")

    browser.close()
