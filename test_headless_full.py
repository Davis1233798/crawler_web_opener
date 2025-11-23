import asyncio
from playwright.async_api import async_playwright

async def main():
    print("Launching browser with headless=True and full args...")
    
    # Mimic BrowserBot launch args exactly
    launch_args = ['--disable-blink-features=AutomationControlled']
    
    # Mimic proxy config (using a dummy one or None to start)
    # We'll try without proxy first, as we just want to check if args break headless
    proxy_config = None 
    
    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(
                headless=True,
                proxy=proxy_config,
                args=launch_args
            )
            print("Browser launched.")
            
            context = await browser.new_context(viewport={'width': 1280, 'height': 720})
            page = await context.new_page()
            
            await page.goto("http://example.com")
            print("Page loaded. Title:", await page.title())
            print("If you see a browser window, headless mode is NOT working with these args.")
            
            await asyncio.sleep(5)
            await browser.close()
            print("Browser closed.")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
