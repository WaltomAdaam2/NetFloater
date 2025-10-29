import os
import sys

class AutoStartManager:
    def __init__(self):
        self.startup_folder = self.get_startup_folder()
    
    def get_startup_folder(self):
        """Get Windows startup folder path"""
        return os.path.join(
            os.getenv('APPDATA'), 
            'Microsoft', 'Windows', 'Start Menu', 
            'Programs', 'Startup'
        )
    
    def is_enabled(self):
        """Check if auto-start is enabled"""
        bat_path = os.path.join(self.startup_folder, "NetFloater.bat")
        return os.path.exists(bat_path)
    
    def enable(self):
        """Enable auto-start on boot"""
        try:
            if not os.path.exists(self.startup_folder):
                os.makedirs(self.startup_folder)
            
            # Get current executable path
            if hasattr(sys, '_MEIPASS'):
                exe_path = sys.executable
            else:
                exe_path = sys.argv[0]
            
            # Create batch file
            bat_path = os.path.join(self.startup_folder, "NetFloater.bat")
            with open(bat_path, 'w', encoding='utf-8') as f:
                f.write(f'@echo off\n"{exe_path}"\n')
            
            # Hide batch file
            os.system(f'attrib +h "{bat_path}"')
            return True
        except Exception as e:
            print(f"Failed to enable auto-start: {e}")
            return False
    
    def disable(self):
        """Disable auto-start on boot"""
        try:
            bat_path = os.path.join(self.startup_folder, "NetFloater.bat")
            if os.path.exists(bat_path):
                os.remove(bat_path)
            return True
        except Exception as e:
            print(f"Failed to disable auto-start: {e}")
            return False