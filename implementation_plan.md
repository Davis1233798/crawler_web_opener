# Optimization Implementation Plan

## Goal Description
Optimize the crawler's viewing efficiency, which has dropped by 50%. The primary focus is on removing bad proxies from the pool immediately upon failure and tuning timeouts to fail fast.

## User Review Required
> [!IMPORTANT]
> I will be modifying `BrowserBot` to interact with `MemoryProxyPool`. This introduces a dependency between the bot and the proxy pool.

## Proposed Changes

### Core Logic

#### [MODIFY] [browser_bot.py](file:///c:/Users/solidityDeveloper/crawler_web_opener/browser_bot.py)
- Update `__init__` to accept `proxy_pool`.
- In `run` method:
    - If `page.goto` fails or times out, call `self.proxy_pool.mark_failed(proxy)`.
    - Reduce `page.goto` timeout from 60s to 30s.

#### [MODIFY] [main.py](file:///c:/Users/solidityDeveloper/crawler_web_opener/main.py)
- Pass `proxy_pool` when initializing `BrowserBot`.

#### [MODIFY] [memory_proxy_pool.py](file:///c:/Users/solidityDeveloper/crawler_web_opener/memory_proxy_pool.py)
- Ensure `mark_failed` efficiently removes the proxy and adds it to `failed_proxies`.
- Add logic to avoid re-adding recently failed proxies during refill.

#### [MODIFY] [proxy_manager.py](file:///c:/Users/solidityDeveloper/crawler_web_opener/proxy_manager.py)
- Reduce `check_proxy` timeout from 10s to 5s to speed up validation.
- Add latency tracking (optional, but good for "efficiency").

## Verification Plan

### Automated Tests
- Run `test_io_performance.py` (if applicable) or create a new test script `test_optimization.py` that:
    - Mocks `BrowserPool` and `MemoryProxyPool`.
    - Simulates a proxy failure.
    - Verifies that `mark_failed` is called and the proxy is removed.

### Manual Verification
- Run `main.py` and observe logs.
- Check if "Marked proxy as failed" logs appear.
- Monitor `tasks_completed` vs `tasks_failed` via logs or metrics.
