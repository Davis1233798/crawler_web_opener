# 低成本 I/O 優化重構計劃

## 目標
大幅降低系統 I/O 操作,提升性能,同時維持低成本。

## 當前 I/O 瓶頸分析

### 🔴 高頻 I/O 操作
1. **Browser 實例管理**: 每個任務都創建/銷毀 browser (磁碟讀取 Chromium 二進制)
2. **Proxy 文件讀寫**: 頻繁讀寫 `proxies.txt` (每次 producer 循環)
3. **配置文件讀取**: 重複載入 `.env` 和 `target_site.txt`
4. **日誌寫入**: 高頻日誌直接寫入磁碟

### 💰 成本影響
- CPU/記憶體: 每次 browser 啟動消耗 200-500MB
- 磁碟 I/O: 每次啟動約 50-100MB 讀取
- **預估降低**: 80-90% I/O,節省 60-70% 資源

---

## 優化方案

### 1️⃣ Browser 池化機制 (預估降低 70% I/O)

#### 當前問題
```python
# 每個 worker 都共用一個 bot 實例,但每次 run() 都創建新 browser
async def run(self, url, proxy=None):
    async with async_playwright() as p:
        browser = await p.chromium.launch()  # ❌ 每次都啟動
```

#### 優化方案
```python
# Browser Pool: 預先啟動 N 個 browser,重用 Context
class BrowserPool:
    def __init__(self, pool_size=5):
        self.browsers = []
        self.pool_size = pool_size
    
    async def get_context(self, proxy, fingerprint):
        """從池中獲取 browser,創建新 context"""
        browser = random.choice(self.browsers)
        return await browser.new_context(proxy=proxy, **fingerprint)
    
    async def initialize(self):
        for _ in range(self.pool_size):
            browser = await playwright.chromium.launch()
            self.browsers.append(browser)
```

**優點**:
- Browser 啟動次數從 N 次降為固定 5 次
- Context 創建成本遠低於 Browser 啟動
- 自動負載均衡

---

### 2️⃣ 內存代理池 (預估降低 95% Proxy I/O)

#### 當前問題
```python
# proxy_manager.py 每次都讀寫文件
def load_proxies_from_file():  # ❌ 頻繁磁碟讀取
    with open("proxies.txt", "r") as f:
        return set(line.strip() for line in f)

def save_proxies_to_file():  # ❌ 頻繁磁碟寫入
    with open("proxies.txt", "w") as f:
        ...
```

#### 優化方案
```python
class MemoryProxyPool:
    def __init__(self, cache_file="proxies.txt"):
        self.working_proxies = []  # 內存池
        self.cache_file = cache_file
        self.last_save_time = 0
        
    async def initialize(self):
        """啟動時從文件載入一次"""
        if os.path.exists(self.cache_file):
            with open(self.cache_file, "r") as f:
                self.working_proxies = [l.strip() for l in f]
    
    def get_proxy(self):
        """從內存獲取"""
        return random.choice(self.working_proxies) if self.working_proxies else None
    
    async def periodic_save(self):
        """每 5 分鐘保存一次(非阻塞)"""
        while True:
            await asyncio.sleep(300)
            await asyncio.to_thread(self._save_to_disk)
```

**優點**:
- 磁碟讀寫從每秒數次降為每 5 分鐘 1 次
- 支持優雅關閉時保存

---

### 3️⃣ 輕量級指紋生成 (預估降低 50% 指紋 I/O)

#### 優化方案
```python
# 預生成指紋模板,隨機組合
FINGERPRINT_TEMPLATES = [
    {
        'viewport': {'width': 1920, 'height': 1080},
        'locale': 'en-US',
        'timezone_id': 'America/New_York'
    },
    {
        'viewport': {'width': 1366, 'height': 768},
        'locale': 'zh-TW',
        'timezone_id': 'Asia/Taipei'
    },
    # ... 10 種模板
]

def get_random_fingerprint():
    """O(1) 指紋生成"""
    template = random.choice(FINGERPRINT_TEMPLATES)
    return {
        **template,
        'user_agent': USER_AGENTS[random.randint(0, len(USER_AGENTS)-1)]
    }
```

**優點**:
- 不依賴外部庫 (playwright-stealth 需要額外 I/O)
- 極快生成速度
- 仍有足夠隨機性

---

### 4️⃣ 配置熱重載 (降低啟動 I/O)

```python
class ConfigManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.targets = []
            cls._instance.load_once()
        return cls._instance
    
    def load_once(self):
        """啟動時載入一次"""
        load_dotenv()  # 只執行一次
        with open("target_site.txt") as f:
            self.targets = [l.strip() for l in f if l.strip()]
```

---

### 5️⃣ 日誌緩衝 (降低日誌 I/O)

```python
# 使用異步日誌處理器
logging.basicConfig(
    level=logging.INFO,
    handlers=[
        logging.handlers.MemoryHandler(
            capacity=100,  # 累積 100 條再寫入
            target=logging.FileHandler("app.log")
        )
    ]
)
```

---

## 預估效果

| 項目 | 當前 | 優化後 | 降低幅度 |
|------|------|--------|----------|
| Browser 啟動 I/O | ~100MB/任務 | ~20MB/批次 | **85%** ↓ |
| Proxy 文件 I/O | ~10次/秒 | ~1次/5分鐘 | **95%** ↓ |
| 配置讀取 | 每次啟動 | 僅啟動時 | **100%** ↓ |
| 日誌 I/O | 實時寫入 | 批次寫入 | **80%** ↓ |
| **總體 I/O** | 基準 | - | **~85%** ↓ |

---

## 成本分析

### 硬體需求變化
- **原方案**: 10 線程 = ~5GB RAM (每個 browser 500MB)
- **優化後**: 10 線程 = ~2.5GB RAM (5 個池化 browser)
- **節省**: 50% 記憶體,可提升至 20 線程

### 代碼複雜度
- 新增代碼: ~200 行
- 重構成本: 低 (向後兼容)
- 維護成本: 無增加

---

## 待實作文件

### 新增文件

#### [NEW] `browser_pool.py`
Browser 池化管理器,負責維護 browser 實例池和分配 context

#### [NEW] `memory_proxy_pool.py`
內存代理池管理器,替代文件讀寫操作

#### [NEW] `fingerprint_generator.py`
輕量級指紋生成器,提供快速隨機指紋

### 修改文件

#### [MODIFY] `browser_bot.py`
重構為使用 Browser Pool,移除每次創建 browser 的邏輯

#### [MODIFY] `main.py`
整合 Browser Pool 和 Memory Proxy Pool,移除頻繁配置讀取

#### [MODIFY] `proxy_manager.py`
保留作為備份,添加與 Memory Pool 的兼容接口

---

## 需要確認的問題

> **重要**: 以下問題需要您確認後才能開始實作

1. **是否接受 5 個常駐 Browser 進程?** (會佔用約 2.5GB 記憶體)
2. **代理池是否可接受 5 分鐘保存間隔?** (異常關閉可能遺失部分代理)
3. **是否需要保留原有的文件讀寫邏輯作為備份?** (增加代碼複雜度)

---

## 驗證計劃

### 自動化測試
```bash
# I/O 監控腳本
python test_io_performance.py --duration 600  # 10 分鐘測試
```

### 手動驗證
1. 使用 `Process Monitor` (Windows) 監控磁碟 I/O
2. 驗證 10 分鐘運行期間的文件讀寫次數
3. 對比優化前後的 CPU/RAM 使用率
4. 確認 Browser 實例數量穩定在池大小範圍內
