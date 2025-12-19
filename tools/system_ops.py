"""System operations tool."""

import psutil
import subprocess
import platform
from .base import BaseTool
from .registry import register_tool


@register_tool
class SystemOpsTool(BaseTool):
    """Monitor system stats and control apps."""
    
    name = "system_ops"
    description = "Check system stats (CPU/RAM/Battery) or open applications"
    
    def run(self, operation: str, app_name: str = None) -> dict:
        """
        Execute system operation.
        
        Args:
            operation: "stats" or "open_app"
            app_name: Name of app to open (required for open_app)
        """
        if operation == "stats":
            return self._get_stats()
        elif operation == "open_app":
            if not app_name:
                return {"error": "app_name required for open_app"}
            return self._open_app(app_name)
        else:
            return {"error": f"Unknown operation: {operation}"}

    def _get_stats(self) -> dict:
        """Get system statistics."""
        stats = {
            "system": platform.system(),
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
        }
        
        # Battery (if available)
        battery = psutil.sensors_battery()
        if battery:
            stats["battery_percent"] = battery.percent
            stats["power_plugged"] = battery.power_plugged
            
        return stats

    def _open_app(self, app_name: str) -> dict:
        """Open an application on macOS."""
        if platform.system() != "Darwin":
            return {"error": "App control only supported on macOS"}
            
        try:
            subprocess.run(["open", "-a", app_name], check=True)
            return {"success": True, "message": f"Opened {app_name}"}
        except subprocess.CalledProcessError:
            return {"error": f"Failed to open {app_name}. Is it installed?"}
