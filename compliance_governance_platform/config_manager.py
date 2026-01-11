"""
Configuration Management Module

Handles configuration loading and management for the Compliance & Governance Platform.
"""

import json
import os
from pathlib import Path
from typing import Dict, Optional


class ConfigManager:
    """
    Manages configuration for the Compliance & Governance Platform.
    """
    
    def __init__(self, config_path: str = "config.json"):
        """
        Initialize the configuration manager.
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = Path(config_path)
        self.config = self.load_config()
    
    def load_config(self) -> Dict:
        """
        Load configuration from file, or create default config if file doesn't exist.
        
        Returns:
            Configuration dictionary
        """
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError as e:
                print(f"Error parsing config file: {e}")
                print("Using default configuration")
                return self._get_default_config()
        else:
            # Create default config file
            default_config = self._get_default_config()
            self.save_config(default_config)
            return default_config
    
    def save_config(self, config: Optional[Dict] = None) -> None:
        """
        Save configuration to file.
        
        Args:
            config: Configuration dictionary (if None, saves current config)
        """
        if config is None:
            config = self.config
        
        with open(self.config_path, 'w') as f:
            json.dump(config, f, indent=2)
    
    def _get_default_config(self) -> Dict:
        """
        Get default configuration.
        
        Returns:
            Default configuration dictionary
        """
        return {
            "database": {
                "path": "compliance_governance.db",
                "echo": False
            },
            "notifications": {
                "enabled": False,
                "email": {
                    "smtp_server": "",
                    "smtp_port": 587,
                    "username": "",
                    "password": ""
                }
            },
            "reminders": {
                "enabled": True,
                "days_ahead": 7
            },
            "evidence": {
                "storage_path": "evidence/"
            }
        }
    
    def get(self, key: str, default: Optional[any] = None) -> any:
        """
        Get a configuration value using dot notation (e.g., "database.path").
        
        Args:
            key: Configuration key (supports dot notation)
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

