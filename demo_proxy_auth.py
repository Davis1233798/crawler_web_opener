"""
演示如何使用帶認證的代理
此腳本展示了新的代理認證功能的使用方法
"""
import asyncio
import logging

from browser_pool import BrowserPool
from memory_proxy_pool import MemoryProxyPool

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

async def demo_authenticated_proxy():
    """演示使用帶認證的代理"""
    
    print("=" * 60)
    print("代理認證功能演示")
    print("=" * 60)
    
    # 初始化代理池
    print("\n1. 初始化代理池...")
    proxy_pool = MemoryProxyPool(
        cache_file="proxies.txt",
        min_pool_size=5
    )
    await proxy_pool.initialize()
    
    # 獲取代理統計
    stats = proxy_pool.get_stats()
    print(f"   代理池大小: {stats['working_proxies']}")
    
    # 初始化瀏覽器池
    print("\n2. 初始化瀏覽器池...")
    browser_pool = BrowserPool(pool_size=2, headless=True)
    await browser_pool.initialize()
    
    # 獲取並使用代理
    print("\n3. 測試代理...")
    for i in range(3):
        print(f"\n   測試 #{i+1}:")
        
        # 從池中獲取代理
        proxy = await proxy_pool.get_proxy()
        
        if not proxy:
            print("   ❌ 無可用代理")
            continue
        
        # 顯示代理資訊
        print(f"   Server: {proxy['server']}")
        if proxy.get('username'):
            print(f"   認證: {proxy['username'][:20]}... / {proxy['password'][:10]}...")
        else:
            print(f"   認證: 無")
        
        try:
            # 創建帶代理的上下文
            context = await browser_pool.create_context(proxy=proxy)
            page = await context.new_page()
            
            # 訪問測試 URL
            print(f"   正在訪問 httpbin.org...")
            await page.goto("https://httpbin.org/ip", timeout=15000)
            
            # 獲取頁面內容
            content = await page.content()
            if "origin" in content:
                print(f"   ✅ 成功使用代理!")
            else:
                print(f"   ⚠️  頁面載入但無 IP 資訊")
            
            # 關閉上下文
            await browser_pool.close_context(context)
            
        except Exception as e:
            print(f"   ❌ 錯誤: {str(e)[:50]}...")
            # 標記失敗的代理
            proxy_str = f"{proxy['server']}"
            if proxy.get('username'):
                # 重建原始格式
                server = proxy['server'].replace('http://', '').replace('https://', '')
                proxy_str = f"{server}:{proxy['username']}:{proxy['password']}"
            await proxy_pool.mark_failed(proxy_str)
        
        await asyncio.sleep(1)
    
    # 清理
    print("\n4. 清理資源...")
    await browser_pool.shutdown()
    await proxy_pool.shutdown()
    
    print("\n" + "=" * 60)
    print("演示完成!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(demo_authenticated_proxy())
