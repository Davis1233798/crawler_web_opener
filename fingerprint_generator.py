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
    {'vendor': 'Google Inc. (NVIDIA)', 'renderer': 'ANGLE (NVIDIA GeForce RTX 4070 Direct3D11 vs_5_0 ps_5_0)'},
    {'vendor': 'Google Inc. (AMD)', 'renderer': 'ANGLE (AMD Radeon RX 7800 XT Direct3D11 vs_5_0 ps_5_0)'},
]

# 字體列表組合(不同系統有不同預設字體)
FONT_SETS = [
    # Windows 10/11
    ['Arial', 'Calibri', 'Cambria', 'Consolas', 'Times New Roman', 'Segoe UI', 'Verdana'],
    # macOS
    ['Arial', 'Helvetica', 'San Francisco', 'Monaco', 'Courier New', 'Times', 'Verdana'],
    # Linux
    ['DejaVu Sans', 'Liberation Sans', 'Ubuntu', 'Noto Sans', 'Arial', 'FreeSans'],
]

# 音訊上下文指紋變體
AUDIO_CONFIGS = [
    {'sampleRate': 44100, 'channelCount': 2, 'bufferSize': 4096},
    {'sampleRate': 48000, 'channelCount': 2, 'bufferSize': 8192},
    {'sampleRate': 44100, 'channelCount': 1, 'bufferSize': 2048},
]

def get_random_fingerprint():
    """
    生成隨機瀏覽器指紋配置(增強版)
    Returns: dict - Playwright browser context 配置
    """
    template = random.choice(FINGERPRINT_TEMPLATES)
    
    # 隨機屏幕分辨率(略大於 viewport)
    viewport_width = template['viewport']['width']
    viewport_height = template['viewport']['height']
    screen_width = viewport_width + random.randint(0, 200)
    screen_height = viewport_height + random.randint(100, 300)
    
    return {
        'user_agent': random.choice(USER_AGENTS),
        'viewport': template['viewport'],
        'locale': template['locale'],
        'timezone_id': template['timezone_id'],
        'color_scheme': template['color_scheme'],
        'device_scale_factor': random.choice([1, 1.25, 1.5, 2]),
        'is_mobile': False,
        'has_touch': False,
        'screen': {
            'width': screen_width,
            'height': screen_height
        },
        # 額外的隨機化參數(通過 init_script 注入)
        '_extra': {
            'fonts': random.choice(FONT_SETS),
            'audio': random.choice(AUDIO_CONFIGS),
            'webgl': random.choice(WEBGL_CONFIGS),
            'hardware_concurrency': random.randint(4, 16),
            'device_memory': random.choice([4, 8, 16, 32]),
        }
    }

def get_stealth_script(fingerprint_extra=None):
    """
    返回增強版反檢測腳本
    
    Args:
        fingerprint_extra: 額外的指紋參數(來自 get_random_fingerprint)
    """
    # 使用傳入的參數或生成隨機值
    if fingerprint_extra:
        webgl = fingerprint_extra.get('webgl', random.choice(WEBGL_CONFIGS))
        hardware_concurrency = fingerprint_extra.get('hardware_concurrency', random.randint(4, 16))
        device_memory = fingerprint_extra.get('device_memory', random.choice([4, 8, 16, 32]))
        audio_config = fingerprint_extra.get('audio', random.choice(AUDIO_CONFIGS))
        fonts = fingerprint_extra.get('fonts', random.choice(FONT_SETS))
    else:
        webgl = random.choice(WEBGL_CONFIGS)
        hardware_concurrency = random.randint(4, 16)
        device_memory = random.choice([4, 8, 16, 32])
        audio_config = random.choice(AUDIO_CONFIGS)
        fonts = random.choice(FONT_SETS)
    
    # 生成隨機的音訊指紋偏移
    audio_noise = random.uniform(0.0001, 0.0005)
    
    # 生成字體列表 JavaScript 字串
    fonts_js = ', '.join([f"'{font}'" for font in fonts])
    
    return f"""
    (function() {{
        'use strict';
        
        // ===== 基礎反檢測 =====
        
        // 隱藏 webdriver 標識
        Object.defineProperty(navigator, 'webdriver', {{
            get: () => undefined,
            configurable: true
        }});
        
        // 移除 __webdriver_evaluate 等特徵
        delete navigator.__webdriver_evaluate;
        delete navigator.__driver_evaluate;
        delete navigator.__webdriver_script_function;
        delete navigator.__webdriver_script_func;
        delete navigator.__webdriver_script_fn;
        delete navigator.__fxdriver_evaluate;
        delete navigator.__driver_unwrapped;
        delete navigator.__webdriver_unwrapped;
        
        // ===== 硬體資訊隨機化 =====
        
        Object.defineProperty(navigator, 'hardwareConcurrency', {{
            get: () => {hardware_concurrency},
            configurable: true
        }});
        
        Object.defineProperty(navigator, 'deviceMemory', {{
            get: () => {device_memory},
            configurable: true
        }});
        
        // ===== WebGL 指紋偽裝 =====
        
        const getParameter = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(parameter) {{
            if (parameter === 37445) return '{webgl['vendor']}';
            if (parameter === 37446) return '{webgl['renderer']}';
            return getParameter.apply(this, arguments);
        }};
        
        // WebGL2 支持
        if (window.WebGL2RenderingContext) {{
            const getParameter2 = WebGL2RenderingContext.prototype.getParameter;
            WebGL2RenderingContext.prototype.getParameter = function(parameter) {{
                if (parameter === 37445) return '{webgl['vendor']}';
                if (parameter === 37446) return '{webgl['renderer']}';
                return getParameter2.apply(this, arguments);
            }};
        }}
        
        // ===== Canvas 指紋隨機化 =====
        
        const shift = {{
            r: Math.floor(Math.random() * 10) - 5,
            g: Math.floor(Math.random() * 10) - 5,
            b: Math.floor(Math.random() * 10) - 5,
            a: Math.floor(Math.random() * 10) - 5
        }};
        
        const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
        HTMLCanvasElement.prototype.toDataURL = function(type) {{
            const context = this.getContext('2d');
            if (context) {{
                const imageData = context.getImageData(0, 0, this.width, this.height);
                for (let i = 0; i < imageData.data.length; i += 4) {{
                    imageData.data[i] = imageData.data[i] + shift.r;
                    imageData.data[i + 1] = imageData.data[i + 1] + shift.g;
                    imageData.data[i + 2] = imageData.data[i + 2] + shift.b;
                    imageData.data[i + 3] = imageData.data[i + 3] + shift.a;
                }}
                context.putImageData(imageData, 0, 0);
            }}
            return originalToDataURL.apply(this, arguments);
        }};
        
        // ===== 音訊上下文指紋隨機化 =====
        
        const AudioContext = window.AudioContext || window.webkitAudioContext;
        if (AudioContext) {{
            const OriginalAnalyser = AudioContext.prototype.createAnalyser;
            AudioContext.prototype.createAnalyser = function() {{
                const analyser = OriginalAnalyser.call(this);
                const originalGetFloatFrequencyData = analyser.getFloatFrequencyData;
                analyser.getFloatFrequencyData = function(array) {{
                    originalGetFloatFrequencyData.call(this, array);
                    for (let i = 0; i < array.length; i++) {{
                        array[i] += {audio_noise} * (Math.random() - 0.5);
                    }}
                }};
                return analyser;
            }};
        }}
        
        // ===== 字體指紋偽裝 =====
        
        const availableFonts = [{fonts_js}];
        Object.defineProperty(document, 'fonts', {{
            get: () => ({{
                check: (font) => availableFonts.some(f => font.includes(f)),
                ready: Promise.resolve(),
                size: availableFonts.length
            }})
        }});
        
        // ===== WebRTC IP 洩漏防護 =====
        
        const originalRTCPeerConnection = window.RTCPeerConnection;
        if (originalRTCPeerConnection) {{
            window.RTCPeerConnection = function(config) {{
                if (config && config.iceServers) {{
                    config.iceServers = config.iceServers.filter(server => {{
                        return !server.urls || !server.urls.toString().includes('stun');
                    }});
                }}
                return new originalRTCPeerConnection(config);
            }};
        }}
        
        // ===== Chrome 特徵檢測防護 =====
        
        if (navigator.plugins.length === 0) {{
            Object.defineProperty(navigator, 'plugins', {{
                get: () => [
                    {{name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer'}},
                    {{name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai'}},
                    {{name: 'Native Client', filename: 'internal-nacl-plugin'}}
                ]
            }});
        }}
        
        // ===== Permissions API 覆蓋 =====
        
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({{ state: Notification.permission }}) :
                originalQuery(parameters)
        );
        
        // ===== Battery API 隨機化 =====
        
        if (navigator.getBattery) {{
            const originalGetBattery = navigator.getBattery;
            navigator.getBattery = function() {{
                return originalGetBattery.call(this).then(battery => {{
                    Object.defineProperties(battery, {{
                        charging: {{ get: () => Math.random() > 0.5 }},
                        level: {{ get: () => 0.5 + Math.random() * 0.5 }},
                        chargingTime: {{ get: () => Infinity }},
                        dischargingTime: {{ get: () => Math.random() * 10000 + 5000 }}
                    }});
                    return battery;
                }});
            }};
        }}
        
        // ===== Chrome App/Runtime 移除 =====
        
        if (window.chrome) {{
            delete window.chrome.runtime;
            delete window.chrome.loadTimes;
            delete window.chrome.csi;
        }}
        
    }})();
    """

if __name__ == "__main__":
    # 測試
    for i in range(3):
        print(f"Fingerprint {i+1}:")
        print(get_random_fingerprint())
        print()
