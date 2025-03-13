import httpx
import logging
from typing import Any, Dict, List, Union, Iterable
from urllib.parse import urlparse

from shelly_prometheus_exporter.settings import get_settings
from shelly_prometheus_exporter.devices import extract_device_info

logger = logging.getLogger(__name__)

def create_metric_line(name: str, labels: Dict[str, str], value: Union[int, float, bool]) -> str:
    """Create a single metric line with labels in Prometheus format.
    
    Args:
        name: Name of the metric
        labels: Dictionary of label names and values
        value: The metric value
    """
    settings = get_settings()
    labels_str = ','.join(f'{k}="{v}"' for k, v in sorted(labels.items()))
    return f'{settings.METRIC_PREFIX}{name}{{{labels_str}}} {value}'

def create_metric(
    metrics: List[str],
    name: str,
    help_text: str,
    metric_type: str,
    labels: Dict[str, str],
    value: Union[int, float, bool]
) -> None:
    """Helper function to create a single Prometheus metric with help and type information.
    
    Args:
        metrics: List to append the metric lines to
        name: Name of the metric
        help_text: Help text describing the metric
        metric_type: Type of metric (gauge, counter, etc.)
        labels: Dictionary of labels for the metric
        value: The metric value
    """
    metrics.append(f'# HELP {name} {help_text}')
    metrics.append(f'# TYPE {name} {metric_type}')
    labels_normalized = {k: str(v) for k, v in labels.items()}
    metrics.append(create_metric_line(name, labels_normalized, value))

def create_metrics(
    metrics: List[str],
    name: str,
    help_text: str,
    metric_type: str,
    labels_and_values: Iterable[tuple[Dict[str, str], Union[int, float, bool]]]
) -> None:
    """Helper function to create multiple Prometheus metrics of the same type.
    
    Args:
        metrics: List to append the metric lines to
        name: Name of the metric
        help_text: Help text describing the metric
        metric_type: Type of metric (gauge, counter, etc.)
        labels_and_values: Iterable of (labels, value) tuples
    """
    metrics.append(f'# HELP {name} {help_text}')
    metrics.append(f'# TYPE {name} {metric_type}')
    for labels, value in labels_and_values:
        labels_normalized = {k: str(v) for k, v in labels.items()}
        metrics.append(create_metric_line(name, labels_normalized, value))

def convert_to_prometheus_metrics(status: Dict[str, Any], settings: Dict[str, Any], target: str) -> str:
    """Convert Shelly status and settings to Prometheus metrics format."""
    metrics = []
    hostname = urlparse(target).hostname or target
    
    # Extract device info
    device_info = extract_device_info(settings)
    
    # Add device info metric with all labels
    create_metric(
        metrics,
        'shelly_device_info',
        'Device information',
        'gauge',
        {
            'target': hostname,
            'type': device_info['type'],
            'mac': device_info['mac'],
            'hostname': device_info['hostname'],
            'firmware': device_info['firmware']
        },
        1
    )
    
    # Process wifi_sta if available
    if 'wifi_sta' in status:
        wifi = status['wifi_sta']
        create_metric(
            metrics,
            'shelly_wifi_rssi',
            'WiFi RSSI signal strength',
            'gauge',
            {'target': hostname},
            wifi.get('rssi', 0)
        )
        
        create_metric(
            metrics,
            'shelly_wifi_connected',
            'WiFi connection status (0=disconnected, 1=connected)',
            'gauge',
            {'target': hostname, 'ssid': wifi.get('ssid', '')},
            1 if wifi.get('connected', False) else 0
        )
    
    # Process cloud connection status
    if 'cloud' in status:
        cloud = status['cloud']
        create_metric(
            metrics,
            'shelly_cloud_connected',
            'Cloud connection status (0=disconnected, 1=connected)',
            'gauge',
            {'target': hostname},
            1 if cloud.get('connected', False) else 0
        )
        
        create_metric(
            metrics,
            'shelly_cloud_enabled',
            'Cloud functionality enabled status (0=disabled, 1=enabled)',
            'gauge',
            {'target': hostname},
            1 if cloud.get('enabled', False) else 0
        )
    
    # Process MQTT connection status
    if 'mqtt' in status:
        mqtt = status['mqtt']
        create_metric(
            metrics,
            'shelly_mqtt_connected',
            'MQTT connection status (0=disconnected, 1=connected)',
            'gauge',
            {'target': hostname},
            1 if mqtt.get('connected', False) else 0
        )
    
    # Process update information
    if 'has_update' in status:
        create_metric(
            metrics,
            'shelly_has_update',
            'Firmware update availability (0=no update, 1=update available)',
            'gauge',
            {'target': hostname},
            1 if status['has_update'] else 0
        )
    
    if 'update' in status:
        update = status['update']
        create_metric(
            metrics,
            'shelly_update_status',
            'Update status information',
            'gauge',
            {
                'target': hostname,
                'status': update.get('status', 'unknown'),
                'current_version': update.get('old_version', ''),
                'new_version': update.get('new_version', '')
            },
            1
        )
    
    # Process RAM metrics
    if 'ram_total' in status and 'ram_free' in status:
        create_metrics(
            metrics,
            'shelly_ram_bytes',
            'RAM information in bytes',
            'gauge',
            [
                ({'target': hostname, 'type': 'total'}, status['ram_total']),
                ({'target': hostname, 'type': 'free'}, status['ram_free']),
                ({'target': hostname, 'type': 'used'}, status['ram_total'] - status['ram_free'])
            ]
        )
    
    # Process filesystem metrics
    if 'fs_size' in status and 'fs_free' in status:
        create_metrics(
            metrics,
            'shelly_fs_bytes',
            'Filesystem information in bytes',
            'gauge',
            [
                ({'target': hostname, 'type': 'total'}, status['fs_size']),
                ({'target': hostname, 'type': 'free'}, status['fs_free']),
                ({'target': hostname, 'type': 'used'}, status['fs_size'] - status['fs_free'])
            ]
        )
    
    # Process temperature if available
    if 'temperature' in status:
        temp_c = status["temperature"]
        temp_k = temp_c + 273.15
        
        create_metric(
            metrics,
            'shelly_temperature_celsius',
            'Device temperature in Celsius',
            'gauge',
            {'target': hostname},
            temp_c
        )
        
        create_metric(
            metrics,
            'shelly_temperature_kelvin',
            'Device temperature in Kelvin',
            'gauge',
            {'target': hostname},
            temp_k
        )
    
    # Process uptime
    if 'uptime' in status:
        create_metric(
            metrics,
            'shelly_uptime',
            'Device uptime in seconds',
            'counter',
            {'target': hostname},
            status['uptime']
        )
    
    # Process relays if available
    if 'relays' in status:
        create_metrics(
            metrics,
            'shelly_relay_state',
            'Relay state (0=off, 1=on)',
            'gauge',
            [({'target': hostname, 'relay': str(idx)}, 1 if relay.get('ison', False) else 0)
             for idx, relay in enumerate(status['relays'])]
        )
    
    # Process meters if available
    if 'meters' in status:
        # Process each meter's metrics
        for idx, meter in enumerate(status['meters']):
            # Basic power and energy metrics
            if 'power' in meter:
                create_metric(
                    metrics,
                    'shelly_power_watts',
                    'Current power consumption in watts',
                    'gauge',
                    {'target': hostname, 'meter': str(idx)},
                    meter['power']
                )
            
            if 'total' in meter:
                total_wattminutes = meter["total"]
                total_watthours = total_wattminutes / 60.0
                
                create_metric(
                    metrics,
                    'shelly_energy_total_wattminutes',
                    'Total energy consumption in watt-minutes',
                    'counter',
                    {'target': hostname, 'meter': str(idx)},
                    total_wattminutes
                )
                
                create_metric(
                    metrics,
                    'shelly_energy_total_watthours',
                    'Total energy consumption in watt-hours (calculated from watt-minutes)',
                    'counter',
                    {'target': hostname, 'meter': str(idx)},
                    total_watthours
                )
            
            # Overpower value if present
            if 'overpower' in meter:
                create_metric(
                    metrics,
                    'shelly_overpower_watts',
                    'Overpower threshold value in watts',
                    'gauge',
                    {'target': hostname, 'meter': str(idx)},
                    meter['overpower']
                )
            
            # Meter validity
            if 'is_valid' in meter:
                create_metric(
                    metrics,
                    'shelly_meter_valid',
                    'Whether the meter provides valid measurements',
                    'gauge',
                    {'target': hostname, 'meter': str(idx)},
                    1 if meter['is_valid'] else 0
                )
            
            # Timestamp if present
            if 'timestamp' in meter:
                create_metric(
                    metrics,
                    'shelly_meter_timestamp',
                    'Unix timestamp of the last meter measurement',
                    'gauge',
                    {'target': hostname, 'meter': str(idx)},
                    meter['timestamp']
                )
            
            # Last minute energy counters (in both watt-minutes and calculated watt-hours)
            if 'counters' in meter and isinstance(meter['counters'], list):
                create_metrics(
                    metrics,
                    'shelly_energy_wattminutes',
                    'Energy consumption per minute in watt-minutes',
                    'gauge',
                    [({'target': hostname, 'meter': str(idx), 'minute': str(minute)}, value)
                     for minute, value in enumerate(meter['counters'])]
                )
                
                create_metrics(
                    metrics,
                    'shelly_energy_watthours',
                    'Energy consumption per minute in watt-hours (calculated from watt-minutes)',
                    'gauge',
                    [({'target': hostname, 'meter': str(idx), 'minute': str(minute)}, value / 60.0)
                     for minute, value in enumerate(meter['counters'])]
                )
    
    # Add max power if available
    if 'max_power' in settings:
        create_metric(
            metrics,
            'shelly_max_power_watts',
            'Maximum allowed power in watts',
            'gauge',
            {'target': hostname},
            settings['max_power']
        )
    
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