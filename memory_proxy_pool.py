"""
內存代理池管理器
減少磁碟 I/O,使用內存緩存代理列表
支援兩種代理格式:
  1. protocol://ip:port (不帶認證)
  2. ip:port:username:password (帶認證)
"""
import os
import asyncio
import logging
import random
import time
from typing import List, Optional, Dict
from proxy_manager import fetch_all_proxies, check_proxy
import concurrent.futures


def parse_proxy(proxy_str: str) -> Optional[Dict[str, str]]:
    """
    解析代理字符串,支援兩種格式:
    1. protocol://ip:port
    2. ip:port:username:password
    
    Returns:
        Dict with keys: 'server', 'username' (optional), 'password' (optional), 'protocol' (optional)
    """
    if not proxy_str:
        return None
    
    proxy_str = proxy_str.strip()
    
    # 格式 1: protocol://ip:port
    if '://' in proxy_str:
        return {
            'server': proxy_str,
            'username': None,
            'password': None
        }
    
    # 格式 2: ip:port:username:password
    parts = proxy_str.split(':')
    if len(parts) == 4:
        ip, port, username, password = parts
        # 默認使用 http 協議
        return {
            'server': f'http://{ip}:{port}',
            'username': username,
            'password': password
        }
    elif len(parts) == 2:
        # ip:port 格式(無認證)
        ip, port = parts
        return {
            'server': f'http://{ip}:{port}',
            'username': None,
            'password': None
        }
    
    logging.warning(f"Unknown proxy format: {proxy_str}")
    return None

class MemoryProxyPool:
    """內存代理池 - 大幅減少文件 I/O"""
    
    def __init__(self, cache_file="proxies.txt", min_pool_size=20, save_interval=300):
        """
        Args:
            cache_file: 代理緩存文件路徑
            min_pool_size: 最小代理池大小
            save_interval: 保存間隔(秒)
        """
        self.cache_file = cache_file
        self.min_pool_size = min_pool_size
        self.save_interval = save_interval
        
        self.working_proxies: List[str] = []
        self.failed_proxies: set = set()
        self.last_save_time = 0
        self.lock = asyncio.Lock()
        
        self._save_task = None
        self._refill_task = None
        
    async def initialize(self):
        """啟動時從文件載入代理(僅一次 I/O)"""
        logging.info("Initializing Memory Proxy Pool...")
        
        # 從文件載入
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r") as f:
                    self.working_proxies = [line.strip() for line in f if line.strip()]
                logging.info(f"Loaded {len(self.working_proxies)} proxies from cache file.")
            except Exception as e:
                logging.error(f"Failed to load cache file: {e}")
        
        # 如果緩存不足,立即補充
        if len(self.working_proxies) < self.min_pool_size:
            logging.info("Proxy pool too small, fetching new proxies...")
            await self.refill_pool()
        
        # 啟動後台任務
        self._save_task = asyncio.create_task(self._periodic_save())
        self._refill_task = asyncio.create_task(self._periodic_refill())
        
        logging.info(f"Memory Proxy Pool initialized with {len(self.working_proxies)} proxies.")
    
    async def get_proxy(self) -> Optional[Dict[str, str]]:
        """
        從內存獲取代理(無 I/O)
        
        Returns:
            Dict with 'server', 'username', 'password' keys, or None if pool is empty
        """
        async with self.lock:
            if not self.working_proxies:
                logging.warning("Proxy pool is empty!")
                return None
            
            # 隨機選擇並解析
            proxy_str = random.choice(self.working_proxies)
            return parse_proxy(proxy_str)
    
    async def mark_failed(self, proxy: str):
        """標記代理失敗"""
        async with self.lock:
            if proxy in self.working_proxies:
                self.working_proxies.remove(proxy)
                self.failed_proxies.add(proxy)
                logging.info(f"Marked proxy as failed: {proxy}. Pool size: {len(self.working_proxies)}")
    
    async def refill_pool(self):
        """補充代理池"""
        needed = max(self.min_pool_size - len(self.working_proxies), 10)
        
        logging.info(f"Refilling proxy pool, need {needed} proxies...")
        
        # 在線程池中執行(避免阻塞)
        raw_proxies = await asyncio.to_thread(fetch_all_proxies, limit=needed * 5)
        
        # 過濾已存在和失敗的代理
        new_candidates = [
            p for p in raw_proxies 
            if p not in self.working_proxies and p not in self.failed_proxies
        ]
        
        if not new_candidates:
            logging.warning("No new proxy candidates found.")
            return
        
        # 驗證代理
        verified = await self._verify_proxies_batch(new_candidates[:needed * 2])
        
        async with self.lock:
            self.working_proxies.extend(verified)
            logging.info(f"Added {len(verified)} new proxies. Pool size: {len(self.working_proxies)}")
    
    async def _verify_proxies_batch(self, proxies: List[str]) -> List[str]:
        """批量驗證代理"""
        verified = []
        
        def verify_batch(proxy_list):
            results = []
            with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
                future_to_proxy = {executor.submit(check_proxy, p, timeout=8): p for p in proxy_list}
                for future in concurrent.futures.as_completed(future_to_proxy):
                    proxy = future_to_proxy[future]
                    try:
                        if future.result():
                            results.append(proxy)
                    except:
                        pass
            return results
        
        verified = await asyncio.to_thread(verify_batch, proxies)
        logging.info(f"Verified {len(verified)}/{len(proxies)} proxies.")
        return verified
    
    async def _periodic_save(self):
        """定期保存到磁碟(減少 I/O 頻率)"""
        while True:
            try:
                await asyncio.sleep(self.save_interval)
                await self._save_to_disk()
            except asyncio.CancelledError:
                # 關閉時最後保存一次
                await self._save_to_disk()
                break
            except Exception as e:
                logging.error(f"Error in periodic save: {e}")
    
    async def _periodic_refill(self):
        """定期檢查並補充代理池"""
        while True:
            try:
                await asyncio.sleep(60)  # 每分鐘檢查一次
                
                if len(self.working_proxies) < self.min_pool_size:
                    logging.info("Proxy pool running low, refilling...")
                    await self.refill_pool()
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"Error in periodic refill: {e}")
    
    async def _save_to_disk(self):
        """保存到磁碟(非阻塞)"""
        try:
            async with self.lock:
                proxies_copy = self.working_proxies.copy()
            
            # 在線程池中執行寫入
            await asyncio.to_thread(self._write_file, proxies_copy)
            
            self.last_save_time = time.time()
            logging.info(f"Saved {len(proxies_copy)} proxies to disk.")
            
        except Exception as e:
            logging.error(f"Failed to save proxies: {e}")
    
    def _write_file(self, proxies: List[str]):
        """同步寫入文件"""
        with open(self.cache_file, "w") as f:
            for proxy in proxies:
                f.write(f"{proxy}\n")
    
    async def shutdown(self):
        """優雅關閉"""
        logging.info("Shutting down Memory Proxy Pool...")
        
        # 取消後台任務
        if self._save_task:
            self._save_task.cancel()
            await asyncio.gather(self._save_task, return_exceptions=True)
        
        if self._refill_task:
            self._refill_task.cancel()
            await asyncio.gather(self._refill_task, return_exceptions=True)
        
        # 最後保存一次
        await self._save_to_disk()
        
        logging.info("Memory Proxy Pool shutdown complete.")
    
    def get_stats(self):
        """獲取統計資訊"""
        return {
            'working_proxies': len(self.working_proxies),
            'failed_proxies': len(self.failed_proxies),
            'last_save': time.time() - self.last_save_time if self.last_save_time > 0 else None
        }


if __name__ == "__main__":
    async def test():
        pool = MemoryProxyPool(min_pool_size=5)
        await pool.initialize()
        
        for i in range(5):
            proxy = await pool.get_proxy()
            print(f"Got proxy {i+1}: {proxy}")
        
        print(f"Stats: {pool.get_stats()}")
        
        await pool.shutdown()
    
    asyncio.run(test())
