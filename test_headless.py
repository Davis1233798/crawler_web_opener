import asyncio
from playwright.async_api import async_playwright

async def main():
    print("Launching browser with headless=True...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("http://example.com")
        print("Page loaded. Title:", await page.title())
        print("If you see a browser window, headless mode is NOT working.")
        await asyncio.sleep(5)
        await browser.close()
        print("Browser closed.")

if __name__ == "__main__":
    asyncio.run(main())
