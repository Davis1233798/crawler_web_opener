import logging
import os
from proxy_manager import fetch_local_proxies, fetch_all_proxies

# Configure logging
logging.basicConfig(level=logging.INFO)

def test_fetch_local_proxies():
    print("Testing fetch_local_proxies...")
    proxies = fetch_local_proxies()
    print(f"Fetched {len(proxies)} proxies from local file.")
    if len(proxies) > 0:
        print(f"Sample proxy: {proxies[0]}")
    else:
        print("No proxies fetched.")

def test_fetch_all_proxies_type_3():
    print("\nTesting fetch_all_proxies with SCRAPY_TYPE=3...")
    os.environ["SCRAPY_TYPE"] = "3"
    proxies = fetch_all_proxies()
    print(f"Fetched {len(proxies)} proxies with SCRAPY_TYPE=3.")
    if len(proxies) > 0:
        print(f"Sample proxy: {proxies[0]}")
    else:
        print("No proxies fetched.")

if __name__ == "__main__":
    test_fetch_local_proxies()
    test_fetch_all_proxies_type_3()
