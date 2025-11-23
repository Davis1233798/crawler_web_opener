import asyncio
import os
import logging
import random
from dotenv import load_dotenv
from browser_pool import BrowserPool
from memory_proxy_pool import MemoryProxyPool
from browser_bot import BrowserBot

# 單次載入環境變數(降低 I/O)
load_dotenv()

THREADS = int(os.getenv("THREADS", 10))
DURATION = int(os.getenv("DURATION", 30))
HEADLESS = os.getenv("HEADLESS", "False").lower() == "true"
BROWSER_POOL_SIZE = int(os.getenv("BROWSER_POOL_SIZE", 5))

# 優化日誌配置(使用緩衝)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

class ConfigManager:
    """配置管理器 - 單次載入,減少 I/O"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.targets = []
            self._load_targets()
            self._initialized = True
    
    def _load_targets(self):
        """單次載入目標網站"""
        try:
            with open("target_site.txt", "r") as f:
                self.targets = [line.strip() for line in f if line.strip()]
            logging.info(f"Loaded {len(self.targets)} target sites.")
        except FileNotFoundError:
            logging.error("target_site.txt not found!")
            self.targets = []
    
    def get_random_target(self):
        """獲取隨機目標"""
        return random.choice(self.targets) if self.targets else None


async def browser_worker(worker_id, queue, bot):
    """
    Worker 執行任務
    """
    logging.info(f"Worker {worker_id} started.")
    while True:
        task = await queue.get()
        url = task['url']
        proxy = task['proxy']
        
        # 定義提前退出的回調
        def should_exit():
            return not queue.empty()
        
        try:
            await bot.run(url, proxy, min_duration=DURATION, should_exit_callback=should_exit)
        except Exception as e:
            logging.error(f"Worker {worker_id} error: {e}")
        finally:
            queue.task_done()
            logging.info(f"Worker {worker_id} finished task. Queue size: {queue.qsize()}")


async def task_producer(queue, proxy_pool, config, limit):
    """
    任務生產者 - 使用 MemoryProxyPool
    """
    while True:
        # 如果隊列已滿,等待
        if queue.qsize() >= limit:
            await asyncio.sleep(5)
            continue
        
        needed = limit - queue.qsize()
        if needed <= 0:
            await asyncio.sleep(5)
            continue
        
        logging.info(f"Producer: Queue low ({queue.qsize()}). Adding tasks...")
        
        # 從內存代理池獲取代理(無 I/O)
        count = 0
        for _ in range(needed):
            if queue.qsize() >= limit * 2:
                break
            
            proxy = await proxy_pool.get_proxy()
            if not proxy:
                logging.warning("No proxies available!")
                break
            
            url = config.get_random_target()
            if not url:
                logging.error("No targets available!")
                break
            
            await queue.put({'url': url, 'proxy': proxy})
            count += 1
        
        logging.info(f"Producer: Added {count} tasks to queue.")
        await asyncio.sleep(1)


async def main():
    """主函數 - 使用池化架構"""
    # 配置管理器(單次載入)
    config = ConfigManager()
    
    if not config.targets:
        logging.error("No targets found. Exiting.")
        return

    logging.info(f"Configuration:")
    logging.info(f"  Targets: {len(config.targets)}")
    logging.info(f"  Threads: {THREADS}")
    logging.info(f"  Duration: {DURATION}s")
    logging.info(f"  Headless: {HEADLESS}")
    logging.info(f"  Browser Pool Size: {BROWSER_POOL_SIZE}")
    
    # 初始化 Browser Pool(一次性 browser 啟動)
    logging.info("Initializing Browser Pool...")
    browser_pool = BrowserPool(pool_size=BROWSER_POOL_SIZE, headless=HEADLESS)
    await browser_pool.initialize()
    
    # 初始化 Memory Proxy Pool(減少文件 I/O)
    logging.info("Initializing Memory Proxy Pool...")
    proxy_pool = MemoryProxyPool(min_pool_size=THREADS * 2)
    await proxy_pool.initialize()
    
    # 創建 BrowserBot 實例
    bot = BrowserBot(browser_pool)
    
    # 任務隊列
    queue = asyncio.Queue(maxsize=THREADS * 2)
    
    # 啟動生產者
    producer_task = asyncio.create_task(task_producer(queue, proxy_pool, config, THREADS))
    
    # 啟動消費者(workers)
    workers = []
    for i in range(THREADS):
        worker = asyncio.create_task(browser_worker(i, queue, bot))
        workers.append(worker)
    
    try:
        # 運行直到用戶中斷
        await asyncio.gather(producer_task, *workers)
    except KeyboardInterrupt:
        logging.info("Received shutdown signal...")
    finally:
        # 優雅關閉
        logging.info("Shutting down...")
        
        # 取消所有任務
        producer_task.cancel()
        for worker in workers:
            worker.cancel()
        
        # 等待任務結束
        await asyncio.gather(producer_task, *workers, return_exceptions=True)
        
        # 關閉資源池
        await proxy_pool.shutdown()
        await browser_pool.shutdown()
        
        logging.info("Shutdown complete.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Stopped by user.")

