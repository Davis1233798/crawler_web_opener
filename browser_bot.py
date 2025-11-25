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
    def __init__(self, browser_pool, proxy_pool=None):
        """
        Args:
            browser_pool: BrowserPool 實例
            proxy_pool: MemoryProxyPool 實例 (可選，用於回報失敗的代理)
        """
        self.browser_pool = browser_pool
        self.proxy_pool = proxy_pool

    async def human_mouse_move(self, page, start_x, start_y, end_x, end_y):
        """模擬人類自然的滑鼠移動軌跡 (貝塞爾曲線)"""
        steps = random.randint(20, 50)
        for i in range(steps):
            t = i / steps
            # 簡單的線性插值加上隨機擾動，模擬手抖
            x = start_x + (end_x - start_x) * t + random.uniform(-5, 5)
            y = start_y + (end_y - start_y) * t + random.uniform(-5, 5)
            try:
                await page.mouse.move(x, y)
                await asyncio.sleep(random.uniform(0.001, 0.01))
            except:
                pass

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
                # Reduced timeout from 60s to 30s for faster failure detection
                await page.goto(url, timeout=30000, wait_until='networkidle')
                
                # Double check load state
                await page.wait_for_load_state('domcontentloaded')
                await page.wait_for_load_state('load')
                
                # Small delay to let JS settle
                await asyncio.sleep(random.uniform(2, 4))
                
            except Exception as e:
                logging.error(f"Navigation failed: {e}")
                # Report failed proxy to pool for removal
                if self.proxy_pool and proxy:
                    await self.proxy_pool.mark_failed(proxy)
                    logging.info(f"Marked proxy as failed: {proxy}")
                return

            # Simulate activity
            logging.info(f"Simulating activity for at least {min_duration} seconds...")
            start_time = asyncio.get_event_loop().time()
            
            # 獲取頁面尺寸
            viewport_width = await page.evaluate("window.innerWidth")
            viewport_height = await page.evaluate("window.innerHeight")
            
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

                    # === 擬人化操作 ===
                    action_type = random.choice(['scroll', 'move', 'pause', 'select'])
                    
                    if action_type == 'scroll':
                        # 隨機滾動 (模擬閱讀)
                        scroll_amount = random.randint(100, 500)
                        direction = random.choice([1, 1, 1, -1]) # 更多向下滾動
                        await page.evaluate(f"window.scrollBy(0, {scroll_amount * direction})")
                        await asyncio.sleep(random.uniform(0.5, 2.0))
                        
                    elif action_type == 'move':
                        # 隨機滑鼠移動
                        start_x = random.randint(0, viewport_width)
                        start_y = random.randint(0, viewport_height)
                        end_x = random.randint(0, viewport_width)
                        end_y = random.randint(0, viewport_height)
                        await self.human_mouse_move(page, start_x, start_y, end_x, end_y)
                        
                    elif action_type == 'pause':
                        # 隨機暫停 (模擬思考/閱讀)
                        pause_time = random.uniform(1.0, 5.0)
                        logging.debug(f"Pausing for {pause_time:.1f}s")
                        await asyncio.sleep(pause_time)
                        
                    elif action_type == 'select':
                        # 隨機選擇文本 (偶爾發生)
                        if random.random() < 0.3:
                            try:
                                await page.evaluate("""
                                    const p = document.querySelector('p');
                                    if(p) {
                                        const range = document.createRange();
                                        range.selectNodeContents(p);
                                        const sel = window.getSelection();
                                        sel.removeAllRanges();
                                        sel.addRange(range);
                                    }
                                """)
                                await asyncio.sleep(random.uniform(0.5, 1.5))
                                # 清除選擇
                                await page.evaluate("window.getSelection().removeAllRanges()")
                            except:
                                pass

                    # Find clickable elements (偶爾點擊)
                    if random.random() < 0.2:
                        elements = await page.query_selector_all('a, button, input[type="submit"], div')
                        if elements:
                            element = random.choice(elements)
                            if await element.is_visible():
                                try:
                                    # 模擬滑鼠移動到元素
                                    box = await element.bounding_box()
                                    if box:
                                        await self.human_mouse_move(page, 
                                            random.randint(0, viewport_width), random.randint(0, viewport_height),
                                            box['x'] + box['width']/2, box['y'] + box['height']/2
                                        )
                                        await element.hover(timeout=2000)
                                        await asyncio.sleep(random.uniform(0.2, 0.5))
                                        # 點擊
                                        if random.random() < 0.5:
                                            await element.click(timeout=1000)
                                except Exception:
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

