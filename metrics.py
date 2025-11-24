from prometheus_client import Counter, Gauge, Histogram

class Metrics:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Metrics, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self._initialized:
            # Counters
            self.tasks_completed = Counter('crawler_tasks_completed', 'Total number of successfully completed tasks')
            self.tasks_failed = Counter('crawler_tasks_failed', 'Total number of failed tasks')
            
            # Gauges
            self.active_threads = Gauge('crawler_active_threads', 'Number of currently active browser threads')
            self.queue_size = Gauge('crawler_queue_size', 'Current number of tasks in the queue')
            
            # Histograms
            self.session_duration = Histogram('crawler_session_duration_seconds', 'Duration of browser sessions in seconds', buckets=[10, 30, 60, 120, 300, 600])
            
            self._initialized = True
