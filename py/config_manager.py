import os
import json

class ConfigManager:
    def __init__(self):
        self.config_dir = os.path.join(os.getenv('APPDATA'), 'NetFloater')
        self.config_file = os.path.join(self.config_dir, 'config.json')
        self.config = self.load_config()
    
    def load_config(self):
        """Load configuration file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Failed to load config: {e}")
        
        # Return default config
        return {
            'show_percentage': False,
            'window_position': None,
            'auto_start': False,
            'compact_mode': False
        }
    
    def save_config(self, config_data=None):
        """Save configuration file"""
        try:
            if not os.path.exists(self.config_dir):
                os.makedirs(self.config_dir)
            
            if config_data is None:
                config_data = self.config
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Failed to save config: {e}")
            return False
    
    def get(self, key, default=None):
        return self.config.get(key, default)
    
    def set(self, key, value):
        self.config[key] = value
        self.save_config()