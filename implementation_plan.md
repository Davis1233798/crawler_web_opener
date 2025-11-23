# Implementation Plan - Proxy Web Opener

## Goal
Create a Python script to fetch US proxies, validate them, and use them to drive 10 concurrent browser instances that visit target sites and simulate user activity.

## Proposed Changes

### Configuration
- **.env**: Store configuration like `THREADS=10`, `DURATION=30`.
- **target_site.txt**: List of URLs to visit.

### Components

#### [NEW] `proxy_manager.py`
- Function `fetch_proxies()`:
    - Target: `https://geonode.com/free-proxy-list`
    - Method: Scrape or use internal API to get US proxies.
    - Returns: List of proxy strings (ip:port).
- Function `check_proxy(proxy)`:
    - Validates proxy by connecting to a test site (e.g., google.com or httpbin.org).
    - Returns: Boolean.

#### [NEW] `browser_bot.py`
- Class `BrowserBot`:
    - Uses `playwright`.
    - Method `run(url, proxy)`:
        - Launches browser with proxy.
        - Navigates to `url`.
        - Simulates random clicks for 30 seconds.
        - Closes browser.

#### [NEW] `main.py`
- Loads config.
- Main loop:
    1. `proxies = fetch_proxies()`
    2. `valid_proxies = [p for p in proxies if check_proxy(p)]`
    3. Launch threads/tasks using `valid_proxies` and URLs from `target_site.txt`.
    4. Repeat.

### Dependencies
- `playwright`
- `requests`
- `python-dotenv`
- `fake-useragent`

## Verification Plan
- Run `main.py` and observe console output for proxy fetching and validation.
- Visually verify browser instances (if headless=False) or check logs for successful page visits.
