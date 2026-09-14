import os
import sys
import json
from playwright.sync_api import sync_playwright

URL = "https://api.justwoker.icu/dashboard/overview"
COOKIES_JSON = os.environ.get("JUSTWOKER_COOKIES")

if not COOKIES_JSON:
    print("缺少 JUSTWOKER_COOKIES 环境变量")
    sys.exit(1)


def run():
    raw = json.loads(COOKIES_JSON)
    print(f"读入 {len(raw)} 条 cookie")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        context = browser.new_context(viewport={"width": 1366, "height": 900})

        pw_cookies = []
        for c in raw:
            pw_cookies.append({
                "name": c["name"],
                "value": c["value"],
                "domain": c.get("domain", ".justwoker.icu"),
                "path": c.get("path", "/"),
                "expires": c.get("expires", -1),
                "httpOnly": c.get("httpOnly", False),
                "secure": c.get("secure", True),
                "sameSite": c.get("sameSite", "Lax"),
            })
        context.add_cookies(pw_cookies)

        page = context.new_page()
        page.set_default_timeout(30000)

        print(f"带着 cookie 打开 {URL}")
        page.goto(URL, wait_until="domcontentloaded")
        page.wait_for_timeout(4000)

        page.screenshot(path="after_login.png", full_page=True)
        print(f"当前 URL: {page.url}")
        print(f"页面标题: {page.title()}")

        # 判断是否登录成功：页面里还有没有“登录”按钮 / 密码输入框
        has_login_form = page.locator('input[name="password"]').count() > 0
        print(f"页面是否含密码输入框: {has_login_form}")

        if "/dashboard" in page.url and not has_login_form:
            print("✅ cookie 有效，已进入 dashboard")
        else:
            print("❌ cookie 失效或未登录，请重新导出")

        context.close()
        browser.close()


if __name__ == "__main__":
    run()