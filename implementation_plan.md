# Implementation Plan - Local Proxy Source

## Goal
Enable loading proxies from a local `proxies.json` file when `SCRAPY_TYPE` is set to `3`. Update documentation to reflect this new method and ensure it is in Traditional Chinese.

## Proposed Changes

### Configuration
#### [MODIFY] [.env](file:///c:/Users/solidityDeveloper/crawler_web_opener/.env)
- Change `SCRAPY_TYPE` to `3`.

### Code
#### [MODIFY] [proxy_manager.py](file:///c:/Users/solidityDeveloper/crawler_web_opener/proxy_manager.py)
- Import `json`.
- Add `fetch_local_proxies()` function:
    - Read `proxies.json`.
    - Parse JSON and extract `proxy` field (e.g., "socks5://...").
    - Return list of proxy strings.
- Update `fetch_all_proxies()`:
    - Add logic for `SCRAPY_TYPE == "3"`.
    - Call `fetch_local_proxies()`.

### Documentation
#### [MODIFY] [README.md](file:///c:/Users/solidityDeveloper/crawler_web_opener/README.md)
- Update `SCRAPY_TYPE` description.
- Add explanation for Type 1, 2, and 3 in Traditional Chinese.

## Verification Plan

### Automated Tests
- Run `python proxy_manager.py` to verify it fetches proxies from the local file.
- Check logs for "Fetched X proxies from Local File".
