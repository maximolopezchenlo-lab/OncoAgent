import asyncio
from playwright.async_api import async_playwright

async def capture_screenshot():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1440, "height": 900})
        try:
            # Wait for server to boot up
            import time
            time.sleep(2)
            await page.goto("http://localhost:7860", wait_until="networkidle")
            await page.wait_for_timeout(2000) # Give Gradio time to render
            await page.screenshot(path="ui_screenshot.png", full_page=True)
            print("Screenshot saved to ui_screenshot.png")
        except Exception as e:
            print(f"Failed to capture: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(capture_screenshot())
