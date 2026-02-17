import os
import sys
import importlib.util
from utils.logger import setup_logger

logger = setup_logger(__name__)

class PluginManager:
    """
    Simple Plugin Manager (Singleton)
    
    Loads plugins from 'plugins/' directory and allows execution of hooks.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PluginManager, cls).__new__(cls)
            cls._instance.plugins = []
            cls._instance._load_plugins()
        return cls._instance
    
    def _load_plugins(self):
        """Load python scripts from plugins/ directory"""
        plugin_dir = os.path.join(os.getcwd(), "plugins")
        if not os.path.exists(plugin_dir):
            os.makedirs(plugin_dir)
            
        sys.path.append(plugin_dir)
        
        for filename in os.listdir(plugin_dir):
            if filename.endswith(".py") and not filename.startswith("_"):
                try:
                    module_name = filename[:-3]
                    file_path = os.path.join(plugin_dir, filename)
                    
                    spec = importlib.util.spec_from_file_location(module_name, file_path)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    self.plugins.append(module)
                    logger.info(f"Loaded plugin: {module_name}")
                except Exception as e:
                    logger.error(f"Failed to load plugin {filename}: {e}")
                    
    def hook(self, event_name, **kwargs):
        """
        Execute a hook on all loaded plugins
        
        Args:
            event_name: Name of the function to call (e.g., 'on_test_start')
            kwargs: Arguments to pass to the hook
        """
        for plugin in self.plugins:
            if hasattr(plugin, event_name):
                try:
                    getattr(plugin, event_name)(**kwargs)
                except Exception as e:
                    logger.error(f"Error in plugin {plugin.__name__}.{event_name}: {e}")
