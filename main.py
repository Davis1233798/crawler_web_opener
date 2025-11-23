import asyncio
import os
import logging
import random
from dotenv import load_dotenv
from proxy_manager import get_working_proxies
from browser_bot import BrowserBot

# Load environment variables
load_dotenv()

THREADS = int(os.getenv("THREADS", 10))
DURATION = int(os.getenv("DURATION", 30))

HEADLESS = os.getenv("HEADLESS", "False").lower() == "true"

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_targets():
    try:
        with open("target_site.txt", "r") as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        logging.error("target_site.txt not found!")
        return []

async def browser_worker(worker_id, queue, bot):
    logging.info(f"Worker {worker_id} started.")
    while True:
        task = await queue.get()
        url = task['url']
        proxy = task['proxy']
        
        # Define callback to check if we should stop
        # Stop if there is a new task waiting in the queue
        def should_exit():
            return not queue.empty()
        
        try:
            await bot.run(url, proxy, min_duration=DURATION, should_exit_callback=should_exit)
        except Exception as e:
            logging.error(f"Worker {worker_id} error: {e}")
        finally:
            queue.task_done()
            logging.info(f"Worker {worker_id} finished task. Queue size: {queue.qsize()}")

async def proxy_producer(queue, limit):
    """
    Continuously ensures there are enough proxies in the queue.
    """
    while True:
        # If queue is full enough, wait
        if queue.qsize() >= limit:
            await asyncio.sleep(5)
            continue
            
        needed = limit - queue.qsize()
        if needed <= 0:
            await asyncio.sleep(5)
            continue
            
        logging.info(f"Producer: Queue low ({queue.qsize()}). Fetching proxies...")
        
        # Fetch proxies
        # We use a larger limit for fetching to buffer
        proxies = await asyncio.to_thread(get_working_proxies, limit=needed)
        
        if not proxies:
            logging.warning("Producer: No working proxies found. Retrying in 30s...")
            await asyncio.sleep(30)
            continue
            
        targets = load_targets()
        if not targets:
            logging.error("No targets found!")
            await asyncio.sleep(30)
            continue

        count = 0
        for proxy in proxies:
            if queue.qsize() >= limit * 2: # Don't overfill
                break
            url = random.choice(targets)
            await queue.put({'url': url, 'proxy': proxy})
            count += 1
            
        logging.info(f"Producer: Added {count} tasks to queue.")
        await asyncio.sleep(1)

async def main():
    targets = load_targets()
    if not targets:
        logging.error("No targets found. Exiting.")
        return

    logging.info(f"Loaded {len(targets)} targets. Threads: {THREADS}, Duration: {DURATION}s, Headless: {HEADLESS}")
    print(f"DEBUG: HEADLESS env var is '{os.getenv('HEADLESS')}', parsed as {HEADLESS}")
    
    queue = asyncio.Queue(maxsize=THREADS * 2)
    bot = BrowserBot(headless=HEADLESS)
    
    # Start producer
    producer_task = asyncio.create_task(proxy_producer(queue, THREADS))
    
    # Start consumers (workers)
    workers = []
    for i in range(THREADS):
        t = asyncio.create_task(browser_worker(i, queue, bot))
        workers.append(t)
        
    # Wait for everything (forever)
    await asyncio.gather(producer_task, *workers)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Stopped by user.")
