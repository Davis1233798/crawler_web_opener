import requests
import logging
import concurrent.futures

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

import os
from dotenv import load_dotenv

# Load env to get SCRAPY_TYPE
load_dotenv()

def fetch_geonode_proxies(limit=100):
    """
    Fetches proxies from geonode.com API.
    Returns a list of proxy strings in format 'protocol://ip:port'.
    """
    url = "https://proxylist.geonode.com/api/proxy-list"
    params = {
        "limit": limit,
        "page": 1,
        "sort_by": "lastChecked",
        "sort_type": "desc",
        "filterUpTime": 90,
        "anonymityLevel": "elite",
        "protocols": "http,https,socks4,socks5" 
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        proxies = []
        for item in data.get("data", []):
            ip = item.get("ip")
            port = item.get("port")
            protocols = item.get("protocols", [])
            
            if ip and port:
                protocol = "http"
                if "socks5" in protocols:
                    protocol = "socks5"
                elif "socks4" in protocols:
                    protocol = "socks4"
                elif "https" in protocols:
                    protocol = "http" # Playwright often handles https via http proxy config or just http://
                
                proxy_str = f"{protocol}://{ip}:{port}"
                proxies.append(proxy_str)
        
        logging.info(f"Fetched {len(proxies)} proxies from Geonode.")
        return proxies
        
    except Exception as e:
        logging.error(f"Error fetching Geonode proxies: {e}")
        return []

def fetch_proxyscrape_proxies():
    """
    Fetches proxies from proxyscrape.com API.
    Returns a list of proxy strings in format 'protocol://ip:port'.
    """
    url = "https://api.proxyscrape.com/v4/free-proxy-list/get?request=display_proxies&proxy_format=protocolipport&format=text&anonymity=Elite&timeout=20000"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        # The response is a text file with one proxy per line
        proxies = [line.strip() for line in response.text.splitlines() if line.strip()]
        
        logging.info(f"Fetched {len(proxies)} proxies from ProxyScrape.")
        return proxies
        
    except Exception as e:
        logging.error(f"Error fetching ProxyScrape proxies: {e}")
        return []

def fetch_all_proxies(limit=100):
    """
    Fetches proxies from available sources based on SCRAPY_TYPE.
    SCRAPY_TYPE: 1=Geonode, 2=ProxyScrape, ALL=Both
    """
    proxies = []
    scrapy_type = os.getenv("SCRAPY_TYPE", "ALL").upper()
    
    logging.info(f"Fetching proxies with SCRAPY_TYPE={scrapy_type}")
    
    # Fetch from Geonode (Type 1 or ALL)
    if scrapy_type == "1" or scrapy_type == "ALL":
        proxies.extend(fetch_geonode_proxies(limit))
    
    # Fetch from ProxyScrape (Type 2 or ALL)
    if scrapy_type == "2" or scrapy_type == "ALL":
        proxies.extend(fetch_proxyscrape_proxies())
    
    # Deduplicate
    unique_proxies = list(set(proxies))
    logging.info(f"Total unique proxies fetched: {len(unique_proxies)}")
    return unique_proxies

def check_proxy(proxy_url, timeout=10):
    """
    Validates a proxy by making a request to a test URL.
    """
    test_url = "http://httpbin.org/ip"
    proxies = {
        "http": proxy_url,
        "https": proxy_url
    }
    try:
        response = requests.get(test_url, proxies=proxies, timeout=timeout)
        if response.status_code == 200:
            return True
    except Exception as e:
        # logging.debug(f"Proxy {proxy_url} failed: {e}")
        pass
    return False

def load_proxies_from_file(filename="proxies.txt"):
    try:
        with open(filename, "r") as f:
            return set(line.strip() for line in f if line.strip())
    except FileNotFoundError:
        return set()

def save_proxies_to_file(proxies, filename="proxies.txt"):
    try:
        # Read existing to append only unique
        existing = load_proxies_from_file(filename)
        updated = existing.union(set(proxies))
        with open(filename, "w") as f:
            for proxy in updated:
                f.write(f"{proxy}\n")
    except Exception as e:
        logging.error(f"Error saving proxies: {e}")

def get_working_proxies(limit=10):
    """
    Fetches and validates proxies until we have enough working ones.
    Uses a local cache to store working proxies.
    """
    # 1. Load cached proxies
    cached_proxies = list(load_proxies_from_file())
    working_proxies = []
    
    logging.info(f"Loaded {len(cached_proxies)} cached proxies. Verifying...")
    
    # Helper to verify a list of proxies
    def verify_batch(proxy_list):
        verified = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
            future_to_proxy = {executor.submit(check_proxy, p): p for p in proxy_list}
            for future in concurrent.futures.as_completed(future_to_proxy):
                proxy = future_to_proxy[future]
                try:
                    if future.result():
                        verified.append(proxy)
                except:
                    pass
        return verified

    if cached_proxies:
        working_proxies.extend(verify_batch(cached_proxies))
        logging.info(f"Verified {len(working_proxies)} cached proxies.")

    if len(working_proxies) >= limit:
        return working_proxies

    # 2. Fetch new proxies if needed
    logging.info("Fetching new proxies...")
    # We fetch all available proxies from sources
    raw_proxies = fetch_all_proxies(limit=limit*20) 
    
    new_candidates = [p for p in raw_proxies if p not in cached_proxies]
    logging.info(f"Testing {len(new_candidates)} new candidates...")
    
    verified_new = verify_batch(new_candidates)
    working_proxies.extend(verified_new)
    
    # 3. Save working proxies to file
    if working_proxies:
        save_proxies_to_file(working_proxies)
        
    return working_proxies

if __name__ == "__main__":
    proxies = get_working_proxies(limit=5)
    print(f"Working proxies: {proxies}")
