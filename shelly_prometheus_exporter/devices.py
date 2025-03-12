from typing import Set, Dict, Any
from fastapi import HTTPException

def extract_device_info(settings: Dict[str, Any]) -> Dict[str, str]:
    """
    Extract relevant device information from settings.
    
    Args:
        settings: Device settings dictionary from /settings endpoint
        
    Returns:
        Dictionary containing device information
    """
    device = settings.get('device', {})
    return {
        'type': device.get('type', 'unknown'),
        'mac': device.get('mac', 'unknown'),
        'hostname': device.get('hostname', 'unknown'),
        'firmware': settings.get('fw', 'unknown')
    } 