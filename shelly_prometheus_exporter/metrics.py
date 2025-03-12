import httpx
import logging
from typing import Any, Dict
from urllib.parse import urlparse
from .devices import extract_device_info

logger = logging.getLogger(__name__)

def convert_to_prometheus_metrics(status: Dict[str, Any], settings: Dict[str, Any], target: str) -> str:
    """Convert Shelly status and settings to Prometheus metrics format."""
    metrics = []
    hostname = urlparse(target).hostname or target
    
    # Extract device info
    device_info = extract_device_info(settings)
    
    # Add device info metric with all labels
    metrics.append('# HELP shelly_device_info Device information')
    metrics.append('# TYPE shelly_device_info gauge')
    metrics.append(f'shelly_device_info{{target="{hostname}",type="{device_info["type"]}",mac="{device_info["mac"]}",hostname="{device_info["hostname"]}",firmware="{device_info["firmware"]}"}} 1')
    
    # Process wifi_sta if available
    if 'wifi_sta' in status:
        wifi = status['wifi_sta']
        # RSSI metric
        metrics.append('# HELP shelly_wifi_rssi WiFi RSSI signal strength')
        metrics.append('# TYPE shelly_wifi_rssi gauge')
        metrics.append(f'shelly_wifi_rssi{{target="{hostname}"}} {wifi.get("rssi", 0)}')
        
        # WiFi connection status
        metrics.append('# HELP shelly_wifi_connected WiFi connection status (0=disconnected, 1=connected)')
        metrics.append('# TYPE shelly_wifi_connected gauge')
        metrics.append(f'shelly_wifi_connected{{target="{hostname}",ssid="{wifi.get("ssid", "")}"}} {1 if wifi.get("connected", False) else 0}')
    
    # Process cloud connection status
    if 'cloud' in status:
        cloud = status['cloud']
        metrics.append('# HELP shelly_cloud_connected Cloud connection status (0=disconnected, 1=connected)')
        metrics.append('# TYPE shelly_cloud_connected gauge')
        metrics.append(f'shelly_cloud_connected{{target="{hostname}"}} {1 if cloud.get("connected", False) else 0}')
        
        metrics.append('# HELP shelly_cloud_enabled Cloud functionality enabled status (0=disabled, 1=enabled)')
        metrics.append('# TYPE shelly_cloud_enabled gauge')
        metrics.append(f'shelly_cloud_enabled{{target="{hostname}"}} {1 if cloud.get("enabled", False) else 0}')
    
    # Process MQTT connection status
    if 'mqtt' in status:
        mqtt = status['mqtt']
        metrics.append('# HELP shelly_mqtt_connected MQTT connection status (0=disconnected, 1=connected)')
        metrics.append('# TYPE shelly_mqtt_connected gauge')
        metrics.append(f'shelly_mqtt_connected{{target="{hostname}"}} {1 if mqtt.get("connected", False) else 0}')
    
    # Process update information
    if 'has_update' in status:
        metrics.append('# HELP shelly_has_update Firmware update availability (0=no update, 1=update available)')
        metrics.append('# TYPE shelly_has_update gauge')
        metrics.append(f'shelly_has_update{{target="{hostname}"}} {1 if status["has_update"] else 0}')
    
    if 'update' in status:
        update = status['update']
        metrics.append('# HELP shelly_update_status Update status information')
        metrics.append('# TYPE shelly_update_status gauge')
        metrics.append(f'shelly_update_status{{target="{hostname}",status="{update.get("status", "unknown")}",current_version="{update.get("old_version", "")}",new_version="{update.get("new_version", "")}"}} 1')
    
    # Process RAM metrics
    if 'ram_total' in status and 'ram_free' in status:
        metrics.append('# HELP shelly_ram_bytes RAM information in bytes')
        metrics.append('# TYPE shelly_ram_bytes gauge')
        metrics.append(f'shelly_ram_bytes{{target="{hostname}",type="total"}} {status["ram_total"]}')
        metrics.append(f'shelly_ram_bytes{{target="{hostname}",type="free"}} {status["ram_free"]}')
        metrics.append(f'shelly_ram_bytes{{target="{hostname}",type="used"}} {status["ram_total"] - status["ram_free"]}')
    
    # Process filesystem metrics
    if 'fs_size' in status and 'fs_free' in status:
        metrics.append('# HELP shelly_fs_bytes Filesystem information in bytes')
        metrics.append('# TYPE shelly_fs_bytes gauge')
        metrics.append(f'shelly_fs_bytes{{target="{hostname}",type="total"}} {status["fs_size"]}')
        metrics.append(f'shelly_fs_bytes{{target="{hostname}",type="free"}} {status["fs_free"]}')
        metrics.append(f'shelly_fs_bytes{{target="{hostname}",type="used"}} {status["fs_size"] - status["fs_free"]}')
    
    # Process temperature if available
    if 'temperature' in status:
        temp_c = status["temperature"]
        temp_k = temp_c + 273.15
        
        metrics.append('# HELP shelly_temperature_celsius Device temperature in Celsius')
        metrics.append('# TYPE shelly_temperature_celsius gauge')
        metrics.append(f'shelly_temperature_celsius{{target="{hostname}"}} {temp_c}')
        
        metrics.append('# HELP shelly_temperature_kelvin Device temperature in Kelvin')
        metrics.append('# TYPE shelly_temperature_kelvin gauge')
        metrics.append(f'shelly_temperature_kelvin{{target="{hostname}"}} {temp_k}')
    
    # Process uptime
    if 'uptime' in status:
        metrics.append('# HELP shelly_uptime Device uptime in seconds')
        metrics.append('# TYPE shelly_uptime counter')
        metrics.append(f'shelly_uptime{{target="{hostname}"}} {status["uptime"]}')
    
    # Process relays if available
    if 'relays' in status:
        metrics.append('# HELP shelly_relay_state Relay state (0=off, 1=on)')
        metrics.append('# TYPE shelly_relay_state gauge')
        for idx, relay in enumerate(status['relays']):
            metrics.append(f'shelly_relay_state{{target="{hostname}",relay="{idx}"}} {1 if relay.get("ison", False) else 0}')
    
    # Process meters if available
    if 'meters' in status:
        # Power metrics
        metrics.append('# HELP shelly_power_watts Current power consumption in watts')
        metrics.append('# TYPE shelly_power_watts gauge')
        
        # Energy metrics (raw watt-minutes)
        metrics.append('# HELP shelly_energy_total_wattminutes Total energy consumption in watt-minutes')
        metrics.append('# TYPE shelly_energy_total_wattminutes counter')
        
        # Energy metrics (calculated watt-hours)
        metrics.append('# HELP shelly_energy_total_watthours Total energy consumption in watt-hours (calculated from watt-minutes)')
        metrics.append('# TYPE shelly_energy_total_watthours counter')
        
        # Overpower metrics
        metrics.append('# HELP shelly_overpower_watts Overpower threshold value in watts')
        metrics.append('# TYPE shelly_overpower_watts gauge')
        
        # Counters metrics (last minute energy reports in watt-minutes)
        metrics.append('# HELP shelly_energy_wattminutes Energy consumption per minute in watt-minutes')
        metrics.append('# TYPE shelly_energy_wattminutes gauge')
        
        # Counters metrics (calculated watt-hours)
        metrics.append('# HELP shelly_energy_watthours Energy consumption per minute in watt-hours (calculated from watt-minutes)')
        metrics.append('# TYPE shelly_energy_watthours gauge')
        
        # Validity metric
        metrics.append('# HELP shelly_meter_valid Whether the meter provides valid measurements')
        metrics.append('# TYPE shelly_meter_valid gauge')
        
        # Timestamp metric
        metrics.append('# HELP shelly_meter_timestamp Unix timestamp of the last meter measurement')
        metrics.append('# TYPE shelly_meter_timestamp gauge')
        
        for idx, meter in enumerate(status['meters']):
            # Basic power and energy metrics
            if 'power' in meter:
                metrics.append(f'shelly_power_watts{{target="{hostname}",meter="{idx}"}} {meter["power"]}')
            if 'total' in meter:
                total_wattminutes = meter["total"]
                total_watthours = total_wattminutes / 60.0
                metrics.append(f'shelly_energy_total_wattminutes{{target="{hostname}",meter="{idx}"}} {total_wattminutes}')
                metrics.append(f'shelly_energy_total_watthours{{target="{hostname}",meter="{idx}"}} {total_watthours}')
            
            # Overpower value if present
            if 'overpower' in meter:
                metrics.append(f'shelly_overpower_watts{{target="{hostname}",meter="{idx}"}} {meter["overpower"]}')
            
            # Meter validity
            if 'is_valid' in meter:
                metrics.append(f'shelly_meter_valid{{target="{hostname}",meter="{idx}"}} {1 if meter["is_valid"] else 0}')
            
            # Timestamp if present
            if 'timestamp' in meter:
                metrics.append(f'shelly_meter_timestamp{{target="{hostname}",meter="{idx}"}} {meter["timestamp"]}')
            
            # Last minute energy counters (in both watt-minutes and calculated watt-hours)
            if 'counters' in meter and isinstance(meter['counters'], list):
                for minute, value in enumerate(meter['counters']):
                    wattminutes = value
                    watthours = wattminutes / 60.0
                    metrics.append(f'shelly_energy_wattminutes{{target="{hostname}",meter="{idx}",minute="{minute}"}} {wattminutes}')
                    metrics.append(f'shelly_energy_watthours{{target="{hostname}",meter="{idx}",minute="{minute}"}} {watthours}')
    
    # Add max power if available
    if 'max_power' in settings:
        metrics.append('# HELP shelly_max_power_watts Maximum allowed power in watts')
        metrics.append('# TYPE shelly_max_power_watts gauge')
        metrics.append(f'shelly_max_power_watts{{target="{hostname}"}} {settings["max_power"]}')
    
    return '\n'.join(metrics)

async def fetch_device_metrics(client: httpx.AsyncClient, target_url: str) -> str:
    """Fetch metrics from a single Shelly device."""
    try:
        # First, get device settings
        settings_response = await client.get(f"{target_url}/settings")
        settings_response.raise_for_status()
        settings_data = settings_response.json()
        
        # Get device status
        status_response = await client.get(f"{target_url}/status")
        status_response.raise_for_status()
        status_data = status_response.json()
        
        return convert_to_prometheus_metrics(status_data, settings_data, target_url)
        
    except httpx.TimeoutException:
        logger.error(f"Timeout while fetching metrics from {target_url}")
        return f"# Error: Timeout while fetching metrics from {target_url}"
    except httpx.HTTPError as e:
        logger.error(f"Error fetching metrics from {target_url}: {str(e)}")
        return f"# Error: Failed to fetch metrics from {target_url}: {str(e)}"
    except Exception as e:
        logger.exception(f"Unexpected error while fetching metrics from {target_url}")
        return f"# Error: Internal error while fetching metrics from {target_url}: {str(e)}" 