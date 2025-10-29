import psutil

class NetworkMonitor:
    def __init__(self):
        self.last_bytes = psutil.net_io_counters()
        self.download_speed = 0.0
        self.upload_speed = 0.0
    
    def update_speed(self):
        """Update network speed"""
        now_bytes = psutil.net_io_counters()
        self.download_speed = (now_bytes.bytes_recv - self.last_bytes.bytes_recv) / 1024
        self.upload_speed = (now_bytes.bytes_sent - self.last_bytes.bytes_sent) / 1024
        self.last_bytes = now_bytes
    
    def get_speeds(self):
        """Get current speeds"""
        return {
            'download': self.download_speed,
            'upload': self.upload_speed
        }
    
    def get_formatted_speeds(self):
        """Get formatted speed text"""
        if self.download_speed > 1024:
            dl_text = f"{self.download_speed/1024:.1f} MB/s"
        else:
            dl_text = f"{self.download_speed:.1f} KB/s"
            
        if self.upload_speed > 1024:
            ul_text = f"{self.upload_speed/1024:.1f} MB/s"
        else:
            ul_text = f"{self.upload_speed:.1f} KB/s"
        
        return dl_text, ul_text