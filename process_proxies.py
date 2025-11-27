import os
import glob
import logging
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

PROXY_DIR = "proxy"
OUTPUT_FILE = "proxies.txt"

def extract_ip(proxy_string):
    """
    Extracts the IP address from a proxy string.
    Handles formats like:
    - IP:PORT:USER:PASS
    - IP:PORT
    - http://IP:PORT
    - socks4://IP:PORT
    """
    # Regex to find IPv4 address
    match = re.search(r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})", proxy_string)
    if match:
        return match.group(1)
    return None

def load_existing_ips(filepath):
    """
    Loads existing IPs from the proxies.txt file.
    """
    existing_ips = set()
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    ip = extract_ip(line)
                    if ip:
                        existing_ips.add(ip)
        except Exception as e:
            logging.error(f"Error reading {filepath}: {e}")
    return existing_ips

def process_new_proxies():
    """
    Reads new proxy files, extracts IPs, checks for duplicates,
    appends new proxies to proxies.txt, and deletes processed files.
    """
    if not os.path.exists(PROXY_DIR):
        logging.info(f"Directory {PROXY_DIR} does not exist.")
        return

    files = glob.glob(os.path.join(PROXY_DIR, "*.txt"))
    if not files:
        logging.info("No proxy files found to process.")
        return

    existing_ips = load_existing_ips(OUTPUT_FILE)
    logging.info(f"Loaded {len(existing_ips)} existing IPs from {OUTPUT_FILE}")

    processed_files = []
    new_proxies_to_append = []

    for file_path in files:
        logging.info(f"Processing file: {file_path}")
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            
            file_has_valid_proxies = False
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                ip = extract_ip(line)
                if ip:
                    print(f"Read IP: {ip}") # Print the read IP as requested
                    
                    if ip not in existing_ips:
                        new_proxies_to_append.append(line)
                        existing_ips.add(ip) # Add to set to avoid duplicates within the same batch
                        file_has_valid_proxies = True
                    else:
                        logging.info(f"IP {ip} already exists. Skipping.")
                else:
                    logging.warning(f"Could not extract IP from line: {line}")

            processed_files.append(file_path)

        except Exception as e:
            logging.error(f"Error processing file {file_path}: {e}")

    # Append new proxies to OUTPUT_FILE
    if new_proxies_to_append:
        try:
            with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
                for proxy in new_proxies_to_append:
                    f.write(proxy + "\n")
            logging.info(f"Appended {len(new_proxies_to_append)} new proxies to {OUTPUT_FILE}")
        except Exception as e:
            logging.error(f"Error writing to {OUTPUT_FILE}: {e}")
            return # If writing fails, do not delete files

    # Delete processed files
    for file_path in processed_files:
        try:
            os.remove(file_path)
            logging.info(f"Deleted processed file: {file_path}")
        except Exception as e:
            logging.error(f"Error deleting file {file_path}: {e}")

if __name__ == "__main__":
    process_new_proxies()
