# Proxy Web Opener

A multi-threaded web traffic simulator that uses proxies to visit target websites and simulate user activity.

## Features

- **Concurrent Browsers**: Maintains a fixed number of active browser sessions (default 10).
- **Continuous Operation**: Automatically extends browser sessions if no new proxies are available, ensuring constant activity.
- **Proxy Management**: Fetches free proxies (HTTP/SOCKS) from Geonode, validates them, and caches working ones.
- **Human-like Interaction**: Simulates scrolling and clicking while avoiding popups and keeping interactions on the target page.
- **Cross-Platform**: Runs on Windows, Linux, and macOS.
- **Headless Mode**: Configurable for server environments.

## Installation

1.  **Install Python 3.8+**
2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
3.  **Install Playwright Browsers**:
    ```bash
    playwright install chromium
    # For Linux, you might need dependencies:
    # playwright install-deps
    ```

## Configuration

Create a `.env` file (or edit the existing one):

```ini
THREADS=10
DURATION=30
HEADLESS=false
```

- `THREADS`: Number of concurrent browsers (default 10).
- `DURATION`: Minimum duration (seconds) for each session.
- `HEADLESS`: Set to `true` to run without visible browser windows (required for most Linux servers).
- `SCRAPY_TYPE`: Proxy source selection (1=Geonode, 2=ProxyScrape, ALL=Both). Default is ALL.

Edit `target_site.txt` to add the URLs you want to visit.

## Running

```bash
python main.py
```

## Running with Docker (Recommended for other machines)

1.  **Install Docker and Docker Compose**.
2.  **Run**:
    ```bash
    docker-compose up -d
    ```
    This will build the image and start the crawler in the background.
3.  **View Logs**:
    ```bash
    docker-compose logs -f
    ```
4.  **Stop**:
    ```bash
    docker-compose down
    ```

The `proxies.txt` and `target_site.txt` files are mounted, so you can edit targets or view cached proxies directly on your host machine.

