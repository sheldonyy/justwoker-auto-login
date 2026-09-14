import os
import sys
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeoutError

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

        # ---------- 第一步：关闭开屏公告 ----------
        print("尝试关闭公告弹窗...")
        try:
            close_btn = page.get_by_role("button", name="Close")
            close_btn.wait_for(state="visible", timeout=8000)
            close_btn.click()
            print("已通过 Close 按钮关闭公告")
        except PWTimeoutError:
            try:
                # 备用选择器（根据你提供的复杂选择器简化）
                page.locator("div.bg-muted\/50 button.group\/button").first.click(timeout=5000)
                print("已通过结构选择器关闭公告")
            except Exception as e:
                print(f"关闭公告失败（可能没有弹窗）：{e}")

        # ---------- 第二步：点击 GitHub 登录 ----------
        print("点击 GitHub 登录按钮...")
        try:
            # 优先按按钮文本定位（中文/英文可能不同）
            github_btn = page.get_by_role("button", name="使用 GitHub 继续")
            github_btn.wait_for(state="visible", timeout=10000)
            github_btn.click()
        except Exception:
            try:
                # 退回到你给的选择器路径
                page.locator("#root form div.flex.flex-col.gap-2 > button").first.click()
            except Exception as e:
                print(f"点击 GitHub 登录按钮失败：{e}")

        # 等跳转到 github.com
        try:
            print("等待跳转到 GitHub...")
            page.wait_for_url("**github.com/**", timeout=30000)
        except PWTimeoutError:
            print("未检测到跳转到 github.com，继续尝试后续步骤")

        # ---------- 第三步：填写 GitHub 账号密码 ----------
        print("填写 GitHub 登录信息...")
        try:
            # 如果当前页面是 GitHub 登录页面则填写；否则跳过
            if "github.com" in page.url:
                page.fill('input[name="login"]', GITHUB_USER)
                page.fill('input[name="password"]', GITHUB_PASS)
                # 提交按钮可能是 <input> 或 <button>
                try:
                    page.click('input[type="submit"][name="commit"]')
                except Exception:
                    page.click('button[type="submit"]')
            else:
                print("当前页面不是 GitHub，跳过填写用户名密码")
        except Exception as e:
            print(f"填写或提交登录表单出错：{e}")

        # ---------- 第四步：处理可能的授权页 ----------
        try:
            page.wait_for_url("**github.com/login/oauth/**", timeout=20000)
            print("检测到 OAuth 授权页，尝试点击 Authorize...")
            try:
                page.click('button[name="authorize"]', timeout=10000)
            except Exception:
                try:
                    page.get_by_role("button", name="Authorize").click(timeout=10000)
                except Exception as e:
                    print(f"点击 Authorize 失败：{e}")
        except PWTimeoutError:
            print("未检测到 OAuth 授权页，跳过授权")

        # ---------- 第五步：等待回到目标站点 ----------
        print("等待回到 justwoker...")
        try:
            page.wait_for_url("**justwoker.icu/**", timeout=45000)
        except PWTimeoutError:
            print("返回站点超时，继续尝试检查当前页面状态")

        try:
            page.wait_for_load_state("networkidle", timeout=30000)
        except Exception:
            pass

        # 保存截图供调试
        try:
            page.screenshot(path="after_login.png", full_page=True)
            print("已保存截图: after_login.png")
        except Exception as e:
            print(f"截图失败：{e}")

        print(f"完成，当前 URL: {page.url}")
        if "/dashboard" in page.url:
            print("✅ 登录成功，已进入 dashboard")
        else:
            print("⚠️ 登录后未进入 dashboard，请检查截图")

        context.close()
        browser.close()


if __name__ == "__main__":
    run()
