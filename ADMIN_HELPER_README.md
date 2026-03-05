# Admin Helper Service - Implementation Guide

## Overview

This implementation solves the server configuration problem by using a **separate privileged service** instead of trying to use sudo from within the Flask app.

## Architecture

```
┌─────────────────────┐
│   Flask App         │
│ (timetracker user)  │
│                     │
│  AdminHelperClient  │
└──────────┬──────────┘
           │ writes JSON request
           ↓
    /var/run/timetracker/requests/
           │
           ↓ monitored by
┌─────────────────────┐
│  Admin Helper       │
│  Service (root)     │
│                     │
│  • Sets timezone    │
│  • Configures NTP   │
│  • Validates input  │
└──────────┬──────────┘
           │ writes JSON response
           ↓
    /var/run/timetracker/responses/
           │
           ↓ read by
    ┌──────────────┐
    │  Flask App   │
    └──────────────┘
```

## Components

### 1. **timetracker-admin-helper.py**
- Python service that runs as root
- Monitors `/var/run/timetracker/requests/` for JSON request files
- Processes whitelisted commands:
  - `set_timezone`: Validates and sets system timezone
  - `set_ntp_servers`: Configures NTP servers in timesyncd.conf
  - `enable_ntp`: Enables NTP synchronization
- Writes responses to `/var/run/timetracker/responses/`
- Logs all operations to `/var/log/timetracker-admin-helper.log`

### 2. **admin_helper_client.py**
- Python library imported by Flask app
- Provides simple API:
  ```python
  helper = AdminHelperClient()
  result = helper.set_timezone('America/Chicago')
  result = helper.set_ntp_servers(['time.google.com', 'time.cloudflare.com'])
  result = helper.enable_ntp_sync()
  ```
- Handles file-based communication with helper service
- 10-second timeout for responses

### 3. **timetracker-admin-helper.service**
- Systemd service file
- Runs the helper script as root
- Auto-starts on boot
- Auto-restarts on failure

## Installation

Run the installation script:

```bash
cd /opt/timetracker
sudo bash install_admin_helper.sh
```

This will:
1. Install the helper script to `/usr/local/bin/`
2. Install the systemd service
3. Create queue directories
4. Start the service

Then restart the main timetracker service:

```bash
sudo systemctl restart timetracker
```

## Testing

### 1. Check helper service is running:
```bash
sudo systemctl status timetracker-admin-helper
```

Should show: `Active: active (running)`

### 2. Check logs:
```bash
sudo tail -f /var/log/timetracker-admin-helper.log
```

### 3. Test in web UI:
1. Log in as admin
2. Go to: **Admin → Server Configuration**
3. Try setting timezone to `America/Chicago`
4. Try setting NTP server to `time.google.com`

Both should work without errors!

## Security Features

✅ **Input Validation**: All parameters are validated before execution  
✅ **Command Whitelisting**: Only specific actions are allowed  
✅ **No Sudo in Flask App**: Main app runs without elevated privileges  
✅ **File-based Queue**: Simple, secure inter-process communication  
✅ **Detailed Logging**: All operations logged for audit trail  
✅ **Automatic Cleanup**: Request/response files automatically deleted  

## Troubleshooting

### Helper service won't start
```bash
sudo journalctl -u timetracker-admin-helper -n 50 --no-pager
```

### Requests timeout
- Check helper service is running: `systemctl status timetracker-admin-helper`
- Check queue directories exist: `ls -la /var/run/timetracker/`
- Check permissions: `ls -la /var/run/timetracker/requests/`

### Still getting sudo errors
- Restart Flask app: `sudo systemctl restart timetracker`
- Check Flask app imports AdminHelperClient: `grep AdminHelperClient /opt/timetracker/app.py`

## Advantages Over Sudo Approach

| Feature | Sudo Approach | Helper Service |
|---------|--------------|----------------|
| Works with NoNewPrivileges | ❌ No | ✅ Yes |
| No systemd conflicts | ❌ No | ✅ Yes |
| Detailed logging | ⚠️  Limited | ✅ Yes |
| Input validation | ⚠️  Manual | ✅ Built-in |
| Easy debugging | ❌ No | ✅ Yes |
| Setup complexity | 😐 Medium | 😐 Medium |

## Files Created

- `/usr/local/bin/timetracker-admin-helper` - Helper script
- `/etc/systemd/system/timetracker-admin-helper.service` - Service file
- `/var/run/timetracker/requests/` - Request queue
- `/var/run/timetracker/responses/` - Response queue
- `/var/log/timetracker-admin-helper.log` - Service logs
- `/opt/timetracker/admin_helper_client.py` - Client library (imported by Flask)

## Uninstallation

If you need to remove the helper service:

```bash
sudo systemctl stop timetracker-admin-helper
sudo systemctl disable timetracker-admin-helper
sudo rm /etc/systemd/system/timetracker-admin-helper.service
sudo rm /usr/local/bin/timetracker-admin-helper
sudo systemctl daemon-reload
```

Then revert Flask app to use sudo (or remove server config features).
