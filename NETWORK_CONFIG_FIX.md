# Network Configuration Fix

## Problem

The "Modify Network Configuration" feature in the Server Configuration page was not working because:

1. **Missing integration**: The network configuration code in [app.py:2265](app.py#L2265) was trying to use a sudo-based script (`/usr/local/bin/update-netplan-config`) instead of the admin helper service
2. **Incomplete implementation**: The admin helper service only supported timezone and NTP operations, but not network configuration
3. **Inconsistent approach**: Other server config features (timezone, NTP) use the admin helper service, but network config was using a different sudo-based approach

## Solution

Added network configuration support to the admin helper service architecture:

### 1. Updated Admin Helper Service ([timetracker-admin-helper.py](timetracker-admin-helper.py))

Added a new `set_network_config()` function that:
- Validates IP addresses, subnet masks, gateway, and DNS servers
- Converts subnet masks from dotted notation to CIDR prefix
- Generates netplan YAML configuration
- Backs up existing netplan config before making changes
- Validates and applies netplan configuration
- Handles timeouts gracefully (network changes can cause connection drops)

### 2. Updated Admin Helper Client ([admin_helper_client.py](admin_helper_client.py))

Added `set_network_config()` method that sends network configuration requests to the admin helper service via the queue system.

### 3. Updated Flask App ([app.py](app.py#L2265))

Modified the `/api/admin/set-network-config` route to:
- Use the `AdminHelperClient` instead of sudo commands
- Remove redundant validation (now handled by the helper service)
- Simplify error handling
- Maintain consistent logging for debugging

## Installation

To apply this fix, run as root:

```bash
sudo /opt/timetracker/update_network_support.sh
```

This script will:
1. Install the updated admin helper service
2. Restart the admin helper service
3. Restart the timetracker service
4. Verify both services are running

## Testing

After installation, test the network configuration feature:

1. Navigate to **Admin → Server Configuration**
2. Go to the **Network Configuration** section
3. Enter network settings:
   - IP Address (e.g., 192.168.1.100)
   - Subnet Mask (e.g., 255.255.255.0 or 24)
   - Gateway (e.g., 192.168.1.1)
   - Primary DNS (e.g., 8.8.8.8)
   - Secondary DNS (optional, e.g., 8.8.4.4)
4. Click **Apply Network Settings**

**Note**: Changing network settings may temporarily disconnect your session if the IP address changes.

## Architecture

The network configuration now follows the same pattern as timezone and NTP configuration:

```
[Browser]
    ↓ POST /api/admin/set-network-config
[Flask App (app.py)]
    ↓ AdminHelperClient.set_network_config()
[Queue System]
    /var/run/timetracker/requests/*.json
    ↓
[Admin Helper Service]
    (runs as root)
    ↓ set_network_config()
    ↓ validates, backs up, applies netplan
[System]
    /etc/netplan/50-cloud-init.yaml
    netplan apply
```

## Benefits

1. **Consistent architecture**: All server config operations now use the admin helper service
2. **Better security**: No sudo configuration needed for the timetracker user
3. **Improved reliability**: Proper timeout handling for network changes
4. **Better logging**: All operations logged to `/var/log/timetracker-admin-helper.log`
5. **Automatic backups**: Previous netplan configs backed up to `/opt/timetracker/netplan-backups/`

## Files Changed

- [timetracker-admin-helper.py](timetracker-admin-helper.py) - Added network config support
- [admin_helper_client.py](admin_helper_client.py) - Added client method
- [app.py](app.py#L2265) - Updated to use admin helper service
- [update_network_support.sh](update_network_support.sh) - Installation script

## Logs

Check logs if issues occur:

```bash
# Admin helper logs
sudo journalctl -u timetracker-admin-helper -f

# Timetracker logs
sudo journalctl -u timetracker -f

# Netplan application logs
cat /var/log/netplan-updates.log
```

## Rollback

If issues occur, the previous netplan configuration is automatically backed up:

```bash
# List backups
ls -lh /opt/timetracker/netplan-backups/

# Restore a backup (replace with actual backup filename)
sudo cp /opt/timetracker/netplan-backups/backup-YYYYMMDD-HHMMSS.yaml /etc/netplan/50-cloud-init.yaml
sudo netplan apply
```
