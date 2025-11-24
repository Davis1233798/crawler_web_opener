import requests
import time
import sys

def verify_metrics():
    url = "http://localhost:8000/metrics"
    print(f"Checking metrics at {url}...")
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        content = response.text
        
        # Check for our custom metrics
        required_metrics = [
            "crawler_tasks_completed_total",
            "crawler_tasks_failed_total",
            "crawler_active_threads",
            "crawler_queue_size",
            "crawler_session_duration_seconds_bucket"
        ]
        
        missing = []
        for metric in required_metrics:
            if metric not in content:
                missing.append(metric)
        
        if missing:
            print(f"FAILED: Missing metrics: {missing}")
            sys.exit(1)
            
        print("SUCCESS: All metrics found!")
        print("\nSample output:")
        print("\n".join(content.splitlines()[:10]))
        
    except requests.exceptions.ConnectionError:
        print("FAILED: Could not connect to metrics server. Is the crawler running?")
        sys.exit(1)
    except Exception as e:
        print(f"FAILED: {e}")
        sys.exit(1)

if __name__ == "__main__":
    verify_metrics()
