"""
測試代理解析和認證功能
"""
import asyncio
import sys
sys.path.append('.')

from memory_proxy_pool import parse_proxy

def test_proxy_parsing():
    """測試代理解析功能"""
    print("=== Testing Proxy Parsing ===\n")
    
    # 測試案例
    test_cases = [
        # 格式 1: protocol://ip:port
        "http://139.162.78.109:80",
        "socks4://8.39.228.193:39593",
        "socks5://93.184.4.254:1080",
        
        # 格式 2: ip:port:username:password
        "139.99.55.203:8989:user8343999810-1763992585:8fa50c750f",
        "139.99.86.240:3838:user873325572-1763992572:9932e9ada8",
        "15.235.188.240:9138:user497670303-1763992497:cfaddf0317",
        
        # 格式 3: ip:port (無認證)
        "34.124.190.108:8080",
    ]
    
    for proxy_str in test_cases:
        result = parse_proxy(proxy_str)
        print(f"Input:  {proxy_str}")
        if result:
            print(f"Output: server={result['server']}")
            if result.get('username'):
                print(f"        username={result['username']}, password={result['password']}")
        else:
            print(f"Output: Failed to parse")
        print()

if __name__ == "__main__":
    test_proxy_parsing()
