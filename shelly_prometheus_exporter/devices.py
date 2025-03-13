from typing import Dict, Any

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
        'type': device.get('type', ''),
        'mac': device.get('mac', ''),
        'hostname': device.get('hostname', ''),
        'firmware': settings.get('fw', ''),
        'name': settings.get('name', '')
    } 