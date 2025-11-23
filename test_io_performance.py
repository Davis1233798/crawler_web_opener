"""
I/O 性能測試腳本
比較優化前後的 I/O 操作頻率
"""
import asyncio
import time
from browser_pool import BrowserPool
from memory_proxy_pool import MemoryProxyPool
from browser_bot import BrowserBot

async def test_browser_pool():
    """測試 Browser Pool 性能"""
    print("=" * 60)
    print("測試 Browser Pool 性能")
    print("=" * 60)
    
    pool = BrowserPool(pool_size=3, headless=True)
    
    start_time = time.time()
    await pool.initialize()
    init_time = time.time() - start_time
    
    print(f"✓ 初始化 3 個 browsers: {init_time:.2f}s")
    
    # 測試創建多個 contexts
    start_time = time.time()
    for i in range(10):
        context = await pool.create_context()
        await pool.close_context(context)
    context_time = time.time() - start_time
    
    print(f"✓ 創建+關閉 10 個 contexts: {context_time:.2f}s")
    print(f"✓ 平均每個 context: {context_time/10:.3f}s")
    
    await pool.shutdown()
    print()


async def test_memory_proxy_pool():
    """測試 Memory Proxy Pool 性能"""
    print("=" * 60)
    print("測試 Memory Proxy Pool 性能")
    print("=" * 60)
    
    pool = MemoryProxyPool(min_pool_size=10, save_interval=10)
    
    start_time = time.time()
    await pool.initialize()
    init_time = time.time() - start_time
    
    print(f"✓ 初始化代理池: {init_time:.2f}s")
    
    # 測試獲取代理(純內存操作)
    start_time = time.time()
    for i in range(100):
        proxy = await pool.get_proxy()
    get_time = time.time() - start_time
    
    print(f"✓ 獲取 100 個代理(內存): {get_time:.4f}s")
    print(f"✓ 平均每次: {get_time/100*1000:.2f}ms")
    
    stats = pool.get_stats()
    print(f"✓ 統計: {stats}")
    
    await pool.shutdown()
    print()


async def test_full_workflow():
    """測試完整工作流程"""
    print("=" * 60)
    print("測試完整工作流程")
    print("=" * 60)
    
    # 初始化組件
    browser_pool = BrowserPool(pool_size=2, headless=True)
    await browser_pool.initialize()
    
    proxy_pool = MemoryProxyPool(min_pool_size=5)
    await proxy_pool.initialize()
    
    bot = BrowserBot(browser_pool)
    
    # 運行 3 個任務
    print("運行 3 個瀏覽任務...")
    start_time = time.time()
    
    tasks = []
    for i in range(3):
        proxy = await proxy_pool.get_proxy()
        task = bot.run("https://httpbin.org/headers", proxy=proxy, min_duration=5)
        tasks.append(task)
    
    await asyncio.gather(*tasks)
    
    total_time = time.time() - start_time
    print(f"✓ 完成 3 個任務: {total_time:.2f}s")
    print(f"✓ 平均每個任務: {total_time/3:.2f}s")
    
    # 清理
    await proxy_pool.shutdown()
    await browser_pool.shutdown()
    print()


async def main():
    """運行所有測試"""
    print("\n" + "=" * 60)
    print("I/O 優化性能測試")
    print("=" * 60 + "\n")
    
    try:
        await test_browser_pool()
        await test_memory_proxy_pool()
        await test_full_workflow()
        
        print("=" * 60)
        print("所有測試完成!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
