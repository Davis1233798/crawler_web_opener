"""
Browser 池化管理器
維護固定數量的 Browser 實例,大幅降低啟動 I/O
"""
import asyncio
import logging
import random
from typing import List, Optional
from playwright.async_api import async_playwright, Browser, BrowserContext
from fingerprint_generator import get_random_fingerprint, get_stealth_script

class BrowserPool:
    """Browser 池 - 重用 Browser 實例,只創建新的 Context"""
    
    def __init__(self, pool_size=5, headless=False):
        """
        Args:
            pool_size: Browser 實例數量
            headless: 無頭模式
        """
        self.pool_size = pool_size
        self.headless = headless
        self.browsers: List[Browser] = []
        self.playwright = None
        self.contexts: List[BrowserContext] = []
        
    async def initialize(self):
        """初始化 Browser Pool (一次性 I/O)"""
        logging.info(f"Initializing Browser Pool with {self.pool_size} browsers...")
        
        self.playwright = await async_playwright().start()
        
        # 啟動所有 browser
        for i in range(self.pool_size):
            try:
                # 為每個 browser 生成唯一的啟動參數(增強隔離)
                launch_args = [
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-infobars',
                    '--window-position=0,0',
                    '--ignore-certifcate-errors',
                    '--ignore-certifcate-errors-spki-list',
                    f'--window-size={random.randint(1200, 1920)},{random.randint(800, 1080)}',  # 隨機視窗大小
                ]
                
                launch_headless_param = False
                
                if self.headless:
                    launch_args.append('--headless=new')
                
                browser = await self.playwright.chromium.launch(
                    headless=launch_headless_param,
                    args=launch_args
                )
                self.browsers.append(browser)
                logging.info(f"Browser {i+1}/{self.pool_size} launched successfully.")
            except Exception as e:
                logging.error(f"Failed to launch browser {i+1}: {e}")
        
        if not self.browsers:
            raise RuntimeError("Failed to launch any browsers!")
        
        logging.info(f"Browser Pool initialized with {len(self.browsers)} browsers.")
    
    async def create_context(self, proxy: Optional[str] = None) -> BrowserContext:
        """
        從池中創建新的 Context (低成本操作)
        
        Args:
            proxy: 代理地址
            
        Returns:
            BrowserContext: 新的瀏覽器上下文
        """
        if not self.browsers:
            raise RuntimeError("Browser pool is empty!")
        
        # 隨機選擇一個 browser
        browser = random.choice(self.browsers)
        
        # 生成隨機指紋(增強版)
        fingerprint = get_random_fingerprint()
        
        # 提取額外參數
        fingerprint_extra = fingerprint.pop('_extra', None)
        
        # Proxy 配置
        proxy_config = None
        if proxy:
            proxy_config = {"server": proxy}
        
        # 創建 context (成本遠低於創建 browser)
        context = await browser.new_context(
            proxy=proxy_config,
            **fingerprint
        )
        
        # 注入增強版反檢測腳本
        await context.add_init_script(get_stealth_script(fingerprint_extra))
        
        # 記錄活躍的 context
        self.contexts.append(context)
        
        logging.debug(f"Created context with fingerprint: UA={fingerprint.get('user_agent', 'N/A')[:50]}...")
        
        return context
    
    async def close_context(self, context: BrowserContext):
        """關閉 Context (釋放資源)"""
        try:
            if context in self.contexts:
                self.contexts.remove(context)
            await context.close()
        except Exception as e:
            logging.error(f"Error closing context: {e}")
    
    async def cleanup_old_contexts(self, max_age_seconds=600):
        """清理長時間未使用的 contexts"""
        # 簡化版本:關閉所有非活躍的 contexts
        closed = 0
        for context in self.contexts.copy():
            try:
                # 檢查是否有活躍頁面
                pages = context.pages
                if not pages:
                    await self.close_context(context)
                    closed += 1
            except Exception as e:
                logging.error(f"Error in cleanup: {e}")
        
        if closed > 0:
            logging.info(f"Cleaned up {closed} idle contexts.")
    
    async def shutdown(self):
        """關閉所有 browsers"""
        logging.info("Shutting down Browser Pool...")
        
        # 關閉所有 contexts
        for context in self.contexts.copy():
            await self.close_context(context)
        
        # 關閉所有 browsers
        for browser in self.browsers:
            try:
                await browser.close()
            except Exception as e:
                logging.error(f"Error closing browser: {e}")
        
        # 停止 playwright
        if self.playwright:
            await self.playwright.stop()
        
        logging.info("Browser Pool shutdown complete.")
    
    def get_stats(self):
        """獲取統計資訊"""
        return {
            'total_browsers': len(self.browsers),
            'active_contexts': len(self.contexts),
        }


class BrowserSession:
    """Browser 會話包裝器,自動管理 context 生命週期"""
    
    def __init__(self, pool: BrowserPool, proxy: Optional[str] = None):
        self.pool = pool
        self.proxy = proxy
        self.context: Optional[BrowserContext] = None
    
    async def __aenter__(self):
        """進入時創建 context"""
        self.context = await self.pool.create_context(self.proxy)
        return self.context
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """退出時關閉 context"""
        if self.context:
            await self.pool.close_context(self.context)


if __name__ == "__main__":
    async def test():
        pool = BrowserPool(pool_size=2, headless=True)
        await pool.initialize()
        
        # 測試創建多個 contexts
        for i in range(3):
            async with BrowserSession(pool) as context:
                page = await context.new_page()
                await page.goto("https://httpbin.org/headers")
                await asyncio.sleep(2)
                print(f"Session {i+1} completed")
        
        print(f"Stats: {pool.get_stats()}")
        
        await pool.shutdown()
    
    asyncio.run(test())
