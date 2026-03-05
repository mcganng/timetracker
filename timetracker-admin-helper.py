#!/usr/bin/env python3
"""
Time Tracker Admin Helper Service

This service runs as root and handles privileged operations like:
- Setting system timezone
- Configuring NTP servers
- Network configuration

It monitors a request queue and processes commands, then writes results back.
This allows the main Flask app to request privileged operations without needing sudo.

Security:
- Only accepts specific whitelisted commands
- Input validation on all parameters
- Detailed logging of all operations
- File-based queue with strict permissions
"""

import os
import sys
import time
import json
import subprocess
import logging
from pathlib import Path
from datetime import datetime

# Configuration
QUEUE_DIR = Path("/opt/timetracker/queue/requests")
RESPONSE_DIR = Path("/opt/timetracker/queue/responses")
LOG_FILE = "/var/log/timetracker-admin-helper.log"

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def setup_directories():
    """Create queue and response directories with proper permissions"""
    for directory in [QUEUE_DIR, RESPONSE_DIR]:
        directory.mkdir(parents=True, exist_ok=True)
        # Set permissions: timetracker can write, root can read
        os.chmod(directory, 0o770)
        # Change ownership to timetracker:timetracker
        try:
            subprocess.run(['chown', 'timetracker:timetracker', str(directory)], check=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to set ownership on {directory}: {e}")


def validate_timezone(timezone):
    """Validate timezone is in the valid list"""
    try:
        result = subprocess.run(
            ['/usr/bin/timedatectl', 'list-timezones'],
            capture_output=True,
            text=True,
            check=True
        )
        valid_timezones = result.stdout.strip().split('\n')
        return timezone in valid_timezones
    except subprocess.CalledProcessError:
        logger.error("Failed to get timezone list")
        return False


def set_timezone(timezone):
    """Set system timezone"""
    if not validate_timezone(timezone):
        return {
            'success': False,
            'error': f'Invalid timezone: {timezone}'
        }
    
    try:
        subprocess.run(
            ['/usr/bin/timedatectl', 'set-timezone', timezone],
            check=True,
            capture_output=True,
            text=True
        )
        logger.info(f"Successfully set timezone to: {timezone}")
        return {
            'success': True,
            'message': f'Timezone set to {timezone}'
        }
    except subprocess.CalledProcessError as e:
        error_msg = f"Failed to set timezone: {e.stderr}"
        logger.error(error_msg)
        return {
            'success': False,
            'error': error_msg
        }


def validate_ntp_server(server):
    """Basic validation for NTP server format"""
    # Allow domain names and IP addresses
    if not server or len(server) > 255:
        return False
    # Disallow dangerous characters
    dangerous_chars = [';', '&', '|', '`', '$', '(', ')', '<', '>', '\n', '\r']
    return not any(char in server for char in dangerous_chars)


def set_ntp_servers(servers):
    """Set NTP servers"""
    # Validate all servers
    for server in servers:
        if not validate_ntp_server(server):
            return {
                'success': False,
                'error': f'Invalid NTP server format: {server}'
            }
    
    ntp_config = ' '.join(servers)
    
    try:
        # Backup current config
        backup_file = f"/etc/systemd/timesyncd.conf.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        if os.path.exists('/etc/systemd/timesyncd.conf'):
            subprocess.run(['cp', '/etc/systemd/timesyncd.conf', backup_file], check=True)
        
        # Create new config
        config_content = f"""# Time Tracker - NTP Configuration
# Last updated: {datetime.now()}

[Time]
NTP={ntp_config}
FallbackNTP=time.cloudflare.com time.google.com pool.ntp.org
"""
        
        with open('/etc/systemd/timesyncd.conf', 'w') as f:
            f.write(config_content)
        
        # Restart timesyncd
        subprocess.run(['systemctl', 'restart', 'systemd-timesyncd'], check=True)
        
        # Enable NTP if not already enabled
        subprocess.run(['/usr/bin/timedatectl', 'set-ntp', 'true'], check=True)
        
        logger.info(f"Successfully set NTP servers to: {ntp_config}")
        return {
            'success': True,
            'message': f'NTP servers set to: {ntp_config}'
        }
        
    except Exception as e:
        error_msg = f"Failed to set NTP servers: {str(e)}"
        logger.error(error_msg)
        return {
            'success': False,
            'error': error_msg
        }


def enable_ntp_sync():
    """Enable NTP time synchronization"""
    try:
        subprocess.run(['/usr/bin/timedatectl', 'set-ntp', 'true'], check=True)
        logger.info("Successfully enabled NTP sync")
        return {
            'success': True,
            'message': 'NTP sync enabled'
        }
    except subprocess.CalledProcessError as e:
        error_msg = f"Failed to enable NTP sync: {e.stderr if e.stderr else str(e)}"
        logger.error(error_msg)
        return {
            'success': False,
            'error': error_msg
        }


def process_request(request_data):
    """Process a single request"""
    action = request_data.get('action')
    
    if action == 'set_timezone':
        timezone = request_data.get('timezone')
        return set_timezone(timezone)
    
    elif action == 'set_ntp_servers':
        servers = request_data.get('servers', [])
        return set_ntp_servers(servers)
    
    elif action == 'enable_ntp':
        return enable_ntp_sync()
    
    else:
        return {
            'success': False,
            'error': f'Unknown action: {action}'
        }


def process_queue():
    """Process all pending requests in the queue"""
    for request_file in sorted(QUEUE_DIR.glob('*.json')):
        try:
            # Read request
            with open(request_file, 'r') as f:
                request_data = json.load(f)
            
            logger.info(f"Processing request: {request_file.name}")
            
            # Process request
            result = process_request(request_data)
            
            # Write response
            response_file = RESPONSE_DIR / request_file.name
            with open(response_file, 'w') as f:
                json.dump(result, f)
            
            # Set permissions so timetracker can read it
            os.chmod(response_file, 0o664)
            subprocess.run(['chown', 'timetracker:timetracker', str(response_file)], check=False)
            
            # Remove request file
            request_file.unlink()
            
            logger.info(f"Completed request: {request_file.name}")
            
        except Exception as e:
            logger.error(f"Error processing {request_file}: {e}")
            # Write error response
            try:
                response_file = RESPONSE_DIR / request_file.name
                with open(response_file, 'w') as f:
                    json.dump({
                        'success': False,
                        'error': f'Internal error: {str(e)}'
                    }, f)
                os.chmod(response_file, 0o664)
                subprocess.run(['chown', 'timetracker:timetracker', str(response_file)], check=False)
                request_file.unlink()
            except:
                pass


def main():
    """Main service loop"""
    logger.info("Time Tracker Admin Helper Service starting...")
    
    # Check we're running as root
    if os.geteuid() != 0:
        logger.error("This service must run as root")
        sys.exit(1)
    
    # Setup directories
    setup_directories()
    logger.info("Queue directories created")
    
    logger.info("Service started, monitoring queue...")
    
    # Main loop
    while True:
        try:
            process_queue()
            time.sleep(1)  # Check every second
        except KeyboardInterrupt:
            logger.info("Service stopping...")
            break
        except Exception as e:
            logger.error(f"Unexpected error in main loop: {e}")
            time.sleep(5)  # Wait a bit before retrying


if __name__ == '__main__':
    main()
