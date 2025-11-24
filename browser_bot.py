import asyncio
import random
import logging
from playwright.async_api import BrowserContext
from metrics import Metrics

class BrowserBot:
    """
    重構版 BrowserBot - 使用 BrowserPool 的 context
    不再每次創建新的 browser,大幅降低 I/O
    """
    def __init__(self, browser_pool):
        """
        Args:
            browser_pool: BrowserPool 實例
        """
        self.browser_pool = browser_pool

    async def run(self, url, proxy=None, min_duration=30, should_exit_callback=None):
        """
        使用 browser pool 的 context 訪問 URL 並模擬活動
        
        Args:
            url: 目標 URL
            proxy: 代理地址
            min_duration: 最小持續時間(秒)
            should_exit_callback: 提前退出的回調函數
        """
        logging.info(f"Starting bot for {url} with proxy {proxy}")
        
        # 從 pool 獲取 context (低成本操作,無需啟動新 browser)
        context = None
        try:
            context = await self.browser_pool.create_context(proxy=proxy)
            page = await context.new_page()
            
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
                    if page.is_closed():
                        break

                    # Random scroll
                    await page.evaluate(f"window.scrollBy(0, {random.randint(-100, 300)})")
                    
                    # Find clickable elements
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
                            
                            # Click with lower probability
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
            Metrics().tasks_completed.inc()
            Metrics().session_duration.observe(asyncio.get_event_loop().time() - start_time)
            
        except Exception as e:
            logging.error(f"Browser error: {e}")
            Metrics().tasks_failed.inc()
        finally:
            # 關閉 context,釋放資源 (browser 保留在池中)
            if context:
                await self.browser_pool.close_context(context)


if __name__ == "__main__":
    # Test run (需要先創建 pool)
    from browser_pool import BrowserPool
    
    async def test():
        pool = BrowserPool(pool_size=2, headless=False)
        await pool.initialize()
        
        bot = BrowserBot(pool)
        await bot.run("https://www.example.com", min_duration=10)
        
        await pool.shutdown()
    
    asyncio.run(test())

