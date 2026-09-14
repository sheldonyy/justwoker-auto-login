import os
import sys
from playwright.sync_api import sync_playwright

URL = "https://api.justwoker.icu/dashboard/overview"
GITHUB_USER = os.environ.get("GH_LOGIN_USER")
GITHUB_PASS = os.environ.get("GH_LOGIN_PASS")

if not GITHUB_USER or not GITHUB_PASS:
    print("缺少 GH_LOGIN_USER 或 GH_LOGIN_PASS 环境变量")
    sys.exit(1)


def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
            ],
        )
        context = browser.new_context(
            viewport={"width": 1366, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
        )
        page = context.new_page()
        page.set_default_timeout(30000)

        print(f"打开 {URL}")
        page.goto(URL, wait_until="domcontentloaded")

        # ---------- 第一步：关闭公告弹窗 ----------
        print("尝试关闭公告弹窗...")
        try:
            page.get_by_test_id("notice-dialog-close").click(timeout=8000)
            print("已关闭公告弹窗")
        except Exception as e:
            print(f"没找到公告弹窗（可能没有或已关）：{e}")

        # ---------- 第二步：点击 GitHub 登录 ----------
        print("点击 GitHub 登录按钮...")
        try:
            page.get_by_role("button", name="使用 GitHub 继续").click(timeout=8000)
        except Exception:
            # 兜底：结构选择器
            page.locator(
                "#root form div.flex.flex-col.gap-2 > button"
            ).first.click()
        print("已点击 GitHub 登录")

        # ---------- 第三步：填写 GitHub 账号密码 ----------
        print("等待跳转到 GitHub...")
        page.wait_for_url("**github.com/**", timeout=30000)

        print("填写 GitHub 登录信息...")
        page.fill('input[name="login"]', GITHUB_USER)
        page.fill('input[name="password"]', GITHUB_PASS)
        page.click('input[type="submit"][name="commit"]')

        # ---------- 第四步：处理 OAuth 授权页 ----------
        try:
            page.wait_for_url("**github.com/login/oauth/**", timeout=20000)
            print("检测到 OAuth 授权页，点击 Authorize...")
            page.click('button[name="authorize"]', timeout=10000)
        except Exception:
            print("未检测到 OAuth 授权页，跳过")

        # ---------- 第五步：等待回到目标站点 ----------
        print("等待回到 justwoker...")
        page.wait_for_url("**justwoker.icu/**", timeout=45000)
        page.wait_for_load_state("networkidle", timeout=30000)

        page.screenshot(path="after_login.png", full_page=True)
        print(f"登录完成，当前 URL: {page.url}")

        if "/dashboard" in page.url:
            print("✅ 登录成功，已进入 dashboard")
        else:
            print("⚠️ 登录后未进入 dashboard，请检查截图")

        context.close()
        browser.close()


if __name__ == "__main__":
    run()