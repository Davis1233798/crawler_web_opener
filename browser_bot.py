import asyncio
import random
import logging
from playwright.async_api import async_playwright
from fake_useragent import UserAgent

class BrowserBot:
    def __init__(self, headless=False):
        self.headless = headless
        self.ua = UserAgent()

    async def run(self, url, proxy=None, min_duration=30, should_exit_callback=None):
        """
        Launches browser, visits URL, and simulates activity.
        Runs for at least min_duration. After that, checks should_exit_callback() to decide whether to stop.
        If should_exit_callback is None, stops after min_duration.
        """
        logging.info(f"Starting bot for {url} with proxy {proxy}")
        
        proxy_config = None
        if proxy:
            proxy_config = {
                "server": proxy
            }

        async with async_playwright() as p:
            try:
                # Prepare launch args
                launch_args = ['--disable-blink-features=AutomationControlled']
                
                # Configure headless mode
                # To use the new headless mode (which is more undetectable), we must:
                # 1. Set Playwright's headless=False (so it doesn't add the old --headless flag)
                # 2. Manually add --headless=new to args
                launch_headless_param = False
                
                if self.headless:
                    launch_args.append('--headless=new')
                
                # Launch browser
                logging.info(f"Launching browser... Headless: {self.headless} (Param: {launch_headless_param}), Args: {launch_args}")
                browser = await p.chromium.launch(
                    headless=launch_headless_param,
                    proxy=proxy_config,
                    args=launch_args
                )
                
                # Create context with random user agent
                context = await browser.new_context(
                    user_agent=self.ua.random,
                    viewport={'width': 1280, 'height': 720}
                )
                
                page = await context.new_page()
                
                # Block popups
                page.on("popup", lambda popup: asyncio.create_task(popup.close()))

                # Navigate
                logging.info(f"Navigating to {url}")
                try:
                    # Wait for network idle to ensure page is fully loaded
                    await page.goto(url, timeout=60000, wait_until='networkidle')
                    
                    # Double check load state
                    await page.wait_for_load_state('domcontentloaded')
                    await page.wait_for_load_state('load')
                    
                    # Small delay to let JS settle
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    logging.error(f"Navigation failed: {e}")
                    await browser.close()
                    return

                # Simulate activity
                logging.info(f"Simulating activity for at least {min_duration} seconds...")
                start_time = asyncio.get_event_loop().time()
                
                while True:
                    current_time = asyncio.get_event_loop().time()
                    elapsed = current_time - start_time
                    
                    # Check exit condition
                    if elapsed >= min_duration:
                        if should_exit_callback:
                            if should_exit_callback():
                                logging.info("Exit condition met (new task available). Stopping.")
                                break
                            else:
                                # Log only occasionally to avoid spam
                                if int(elapsed) % 10 == 0:
                                    logging.info(f"Extending session... ({int(elapsed)}s elapsed)")
                        else:
                            break

                    try:
                        # Ensure we are still on the target page (or close to it)
                        # If the page navigated away, we might want to go back or stop?
                        # For now, just continue interacting with the current 'page' object which tracks the tab.
                        
                        if page.is_closed():
                            break

                        # Random scroll
                        await page.evaluate(f"window.scrollBy(0, {random.randint(-100, 300)})")
                        
                        # Random click
                        # Random click
                        # Find clickable elements
                        # We try to avoid target="_blank" to prevent new tabs, but the popup handler should catch them.
                        elements = await page.query_selector_all('a, button, input[type="submit"], div')
                        if elements:
                            element = random.choice(elements)
                            if await element.is_visible():
                                # Hover is safe
                                try:
                                    await element.hover(timeout=2000)
                                except Exception as e:
                                    # If hover fails due to interception, try to remove the intercepting element
                                    if "intercepts pointer events" in str(e):
                                        logging.warning("Element intercepted. Attempting to remove overlay...")
                                        await page.evaluate("""
                                            (function() {
                                                const overlays = document.querySelectorAll('div[znid], div[donto], div[class*="overlay"], div[class*="modal"]');
                                                overlays.forEach(el => el.remove());
                                            })();
                                        """)
                                    pass
                                
                                # Click with lower probability or ensure it doesn't open new window?
                                # The user said "click actions only in target_site page".
                                # We can try to click. If it opens a popup, the handler closes it.
                                try:
                                    await element.click(timeout=1000)
                                except Exception as e:
                                    # Handle click interception similarly
                                    if "intercepts pointer events" in str(e):
                                        logging.warning("Click intercepted. Removing overlays...")
                                        await page.evaluate("""
                                            (function() {
                                                const overlays = document.querySelectorAll('div[znid], div[donto], div[class*="overlay"], div[class*="modal"]');
                                                overlays.forEach(el => el.remove());
                                            })();
                                        """)
                                    pass
                                
                        # Click random position (safe)
                        width = await page.evaluate("window.innerWidth")
                        height = await page.evaluate("window.innerHeight")
                        try:
                            await page.mouse.click(random.randint(0, width), random.randint(0, height))
                        except:
                            pass
                        
                        await asyncio.sleep(random.uniform(0.5, 2.0))
                        
                    except Exception as e:
                        logging.warning(f"Error during simulation: {e}")
                        break
                
                logging.info("Session finished.")
                await browser.close()
                
            except Exception as e:
                logging.error(f"Browser error: {e}")

if __name__ == "__main__":
    # Test run
    bot = BrowserBot(headless=False)
    asyncio.run(bot.run("https://www.example.com", duration=10))
