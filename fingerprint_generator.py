"""
輕量級瀏覽器指紋生成器
提供快速、低 I/O 的隨機指紋生成
"""
import random

# 預定義的 User-Agent 列表
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
]

# 預定義的指紋模板
FINGERPRINT_TEMPLATES = [
    {
        'viewport': {'width': 1920, 'height': 1080},
        'locale': 'en-US',
        'timezone_id': 'America/New_York',
        'color_scheme': 'dark',
    },
    {
        'viewport': {'width': 1366, 'height': 768},
        'locale': 'en-US',
        'timezone_id': 'America/Los_Angeles',
        'color_scheme': 'light',
    },
    {
        'viewport': {'width': 1536, 'height': 864},
        'locale': 'en-GB',
        'timezone_id': 'Europe/London',
        'color_scheme': 'dark',
    },
    {
        'viewport': {'width': 1440, 'height': 900},
        'locale': 'zh-TW',
        'timezone_id': 'Asia/Taipei',
        'color_scheme': 'light',
    },
    {
        'viewport': {'width': 1280, 'height': 720},
        'locale': 'zh-CN',
        'timezone_id': 'Asia/Shanghai',
        'color_scheme': 'dark',
    },
    {
        'viewport': {'width': 2560, 'height': 1440},
        'locale': 'en-US',
        'timezone_id': 'America/Chicago',
        'color_scheme': 'light',
    },
    {
        'viewport': {'width': 1680, 'height': 1050},
        'locale': 'ja-JP',
        'timezone_id': 'Asia/Tokyo',
        'color_scheme': 'dark',
    },
    {
        'viewport': {'width': 1600, 'height': 900},
        'locale': 'ko-KR',
        'timezone_id': 'Asia/Seoul',
        'color_scheme': 'light',
    },
]

# WebGL Vendor/Renderer 組合
WEBGL_CONFIGS = [
    {'vendor': 'Google Inc. (NVIDIA)', 'renderer': 'ANGLE (NVIDIA GeForce RTX 3060 Direct3D11 vs_5_0 ps_5_0)'},
    {'vendor': 'Google Inc. (Intel)', 'renderer': 'ANGLE (Intel(R) UHD Graphics 630 Direct3D11 vs_5_0 ps_5_0)'},
    {'vendor': 'Google Inc. (AMD)', 'renderer': 'ANGLE (AMD Radeon RX 6700 XT Direct3D11 vs_5_0 ps_5_0)'},
    {'vendor': 'Google Inc. (NVIDIA)', 'renderer': 'ANGLE (NVIDIA GeForce GTX 1660 Ti Direct3D11 vs_5_0 ps_5_0)'},
]

def get_random_fingerprint():
    """
    生成隨機瀏覽器指紋配置
    Returns: dict - Playwright browser context 配置
    """
    template = random.choice(FINGERPRINT_TEMPLATES)
    
    return {
        'user_agent': random.choice(USER_AGENTS),
        'viewport': template['viewport'],
        'locale': template['locale'],
        'timezone_id': template['timezone_id'],
        'color_scheme': template['color_scheme'],
        'device_scale_factor': random.choice([1, 1.25, 1.5, 2]),
        'is_mobile': False,
        'has_touch': False,
    }

def get_stealth_script():
    """
    返回反檢測腳本
    """
    webgl = random.choice(WEBGL_CONFIGS)
    hardware_concurrency = random.randint(4, 16)
    device_memory = random.choice([4, 8, 16, 32])
    
    return f"""
    // 隱藏 webdriver 標識
    Object.defineProperty(navigator, 'webdriver', {{
        get: () => undefined
    }});
    
    // 隨機化硬體資訊
    Object.defineProperty(navigator, 'hardwareConcurrency', {{
        get: () => {hardware_concurrency}
    }});
    
    Object.defineProperty(navigator, 'deviceMemory', {{
        get: () => {device_memory}
    }});
    
    // 偽造 WebGL 資訊
    const getParameter = WebGLRenderingContext.prototype.getParameter;
    WebGLRenderingContext.prototype.getParameter = function(parameter) {{
        if (parameter === 37445) {{
            return '{webgl['vendor']}';
        }}
        if (parameter === 37446) {{
            return '{webgl['renderer']}';
        }}
        return getParameter.apply(this, arguments);
    }};
    
    // 防止 Chrome 特徵檢測
    if (navigator.plugins.length === 0) {{
        Object.defineProperty(navigator, 'plugins', {{
            get: () => [
                {{name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer'}},
                {{name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai'}},
                {{name: 'Native Client', filename: 'internal-nacl-plugin'}}
            ]
        }});
    }}
    
    // 覆蓋 permissions API
    const originalQuery = window.navigator.permissions.query;
    window.navigator.permissions.query = (parameters) => (
        parameters.name === 'notifications' ?
            Promise.resolve({{ state: Notification.permission }}) :
            originalQuery(parameters)
    );
    
    // 隨機化 Canvas 指紋
    const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
    HTMLCanvasElement.prototype.toDataURL = function(type) {{
        const shift = {{
            'r': Math.floor(Math.random() * 10) - 5,
            'g': Math.floor(Math.random() * 10) - 5,
            'b': Math.floor(Math.random() * 10) - 5,
            'a': Math.floor(Math.random() * 10) - 5
        }};
        
        const context = this.getContext('2d');
        if (context) {{
            const imageData = context.getImageData(0, 0, this.width, this.height);
            for (let i = 0; i < imageData.data.length; i += 4) {{
                imageData.data[i + 0] = imageData.data[i + 0] + shift['r'];
                imageData.data[i + 1] = imageData.data[i + 1] + shift['g'];
                imageData.data[i + 2] = imageData.data[i + 2] + shift['b'];
                imageData.data[i + 3] = imageData.data[i + 3] + shift['a'];
            }}
            context.putImageData(imageData, 0, 0);
        }}
        
        return originalToDataURL.apply(this, arguments);
    }};
    """

if __name__ == "__main__":
    # 測試
    for i in range(3):
        print(f"Fingerprint {i+1}:")
        print(get_random_fingerprint())
        print()
