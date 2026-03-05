"""
Admin Helper Client Library

This module provides a simple interface for the Flask app to request
privileged operations from the admin helper service.
"""

import json
import time
import uuid
from pathlib import Path


class AdminHelperClient:
    """Client for communicating with the admin helper service"""

    QUEUE_DIR = Path("/opt/timetracker/queue/requests")
    RESPONSE_DIR = Path("/opt/timetracker/queue/responses")
    TIMEOUT = 10  # seconds
    
    def __init__(self):
        """Initialize the client"""
        # Ensure directories exist
        self.QUEUE_DIR.mkdir(parents=True, exist_ok=True)
        self.RESPONSE_DIR.mkdir(parents=True, exist_ok=True)
    
    def _send_request(self, action, **params):
        """
        Send a request to the helper service and wait for response
        
        Args:
            action: The action to perform
            **params: Additional parameters for the action
            
        Returns:
            dict: Response from the helper service
        """
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        request_file = self.QUEUE_DIR / f"{request_id}.json"
        response_file = self.RESPONSE_DIR / f"{request_id}.json"
        
        # Create request
        request_data = {
            'action': action,
            **params
        }
        
        try:
            # Write request to queue
            with open(request_file, 'w') as f:
                json.dump(request_data, f)
            
            # Wait for response
            start_time = time.time()
            while time.time() - start_time < self.TIMEOUT:
                if response_file.exists():
                    # Read response
                    with open(response_file, 'r') as f:
                        response = json.load(f)
                    
                    # Clean up response file
                    try:
                        response_file.unlink()
                    except:
                        pass
                    
                    return response
                
                time.sleep(0.1)  # Check every 100ms
            
            # Timeout
            # Clean up request file if it still exists
            try:
                if request_file.exists():
                    request_file.unlink()
            except:
                pass
            
            return {
                'success': False,
                'error': 'Timeout waiting for admin helper service. Is the service running?'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to communicate with admin helper: {str(e)}'
            }
    
    def set_timezone(self, timezone):
        """
        Set system timezone
        
        Args:
            timezone: The timezone to set (e.g., 'America/Chicago')
            
        Returns:
            dict: {'success': bool, 'message': str} or {'success': False, 'error': str}
        """
        return self._send_request('set_timezone', timezone=timezone)
    
    def set_ntp_servers(self, servers):
        """
        Set NTP servers
        
        Args:
            servers: List of NTP server addresses
            
        Returns:
            dict: {'success': bool, 'message': str} or {'success': False, 'error': str}
        """
        if isinstance(servers, str):
            servers = [s.strip() for s in servers.split() if s.strip()]
        return self._send_request('set_ntp_servers', servers=servers)
    
    def enable_ntp_sync(self):
        """
        Enable NTP time synchronization
        
        Returns:
            dict: {'success': bool, 'message': str} or {'success': False, 'error': str}
        """
        return self._send_request('enable_ntp')
    
    def is_helper_running(self):
        """
        Check if the helper service is running
        
        Returns:
            bool: True if helper is running and responsive
        """
        # Try a simple request with short timeout
        old_timeout = self.TIMEOUT
        self.TIMEOUT = 2
        
        try:
            # This will create a request and wait for response
            # If helper is running, it should respond quickly
            response = self._send_request('ping')
            return response.get('success', False)
        except:
            return False
        finally:
            self.TIMEOUT = old_timeout
