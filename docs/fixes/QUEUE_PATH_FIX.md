# Queue Directory Path Fix

## Problem Found

After adding network configuration support and restarting services, **both timezone and network configuration features stopped working**.

The root cause was a **queue directory path mismatch**:

- **Admin helper service** (`timetracker-admin-helper.py`) was monitoring:
  - `/var/run/timetracker/requests/`
  - `/var/run/timetracker/responses/`

- **Admin helper client** (`admin_helper_client.py`) was writing to:
  - `/opt/timetracker/queue/requests/`
  - `/opt/timetracker/queue/responses/`

This meant the service and client were using completely different directories, so requests were never being processed!

## Evidence from Logs

Looking at the logs after the update:

```bash
# Admin helper service logs showed NO requests being processed
Mar 05 16:15:52 timetracker-admin-helper[1234749]: Service started, monitoring queue...
# No "Processing request:" messages after this point

# Timetracker logs showed requests being SENT
Mar 05 16:16:40 gunicorn[1234780]: POST /api/admin/set-timezone
# But the helper service never saw them
```

## Solution

Updated [admin_helper_client.py](admin_helper_client.py#L17-18) to use the correct paths:

```python
# Before (WRONG)
QUEUE_DIR = Path("/opt/timetracker/queue/requests")
RESPONSE_DIR = Path("/opt/timetracker/queue/responses")

# After (CORRECT)
QUEUE_DIR = Path("/var/run/timetracker/requests")
RESPONSE_DIR = Path("/var/run/timetracker/responses")
```

## Installation

Run the updated installation script:

```bash
sudo /opt/timetracker/update_network_support.sh
```

This will:
1. Install the updated admin helper service
2. Confirm the client is using the correct paths
3. Restart both services
4. Verify both services are running
5. Check that queue directories exist

## Verification

After running the update script, test both features:

### Test Timezone Configuration

1. Go to **Admin → Server Configuration**
2. Click **Time & NTP** section
3. Try changing the timezone
4. Should see success message immediately

### Test Network Configuration

1. Go to **Admin → Server Configuration**
2. Click **Network Configuration** section
3. Enter test network settings (or current settings)
4. Click **Apply Network Settings**
5. Should see success message

### Check Logs

If issues persist, check the logs:

```bash
# Watch admin helper service logs
sudo journalctl -u timetracker-admin-helper -f

# You should see messages like:
# "Processing request: <uuid>.json"
# "Successfully set timezone to: America/Chicago"
# or
# "Netplan applied successfully"
```

## Why This Happened

The path inconsistency was introduced because:

1. The original admin helper service was created with `/var/run/timetracker/` paths (standard for runtime data)
2. The admin helper client was created later with `/opt/timetracker/queue/` paths (which seemed logical at the time)
3. Both worked initially in testing, but when fresh installs happened, the mismatch became apparent

The `/var/run/timetracker/` path is the correct choice because:
- `/var/run/` is the standard location for runtime data in Linux
- It's cleared on reboot (appropriate for temporary request queues)
- It's managed by systemd
- The admin helper service (running as root) can properly set permissions

## Files Changed

- [admin_helper_client.py](admin_helper_client.py) - Fixed queue directory paths
- [update_network_support.sh](update_network_support.sh) - Enhanced installation script

## Complete Fix Summary

**Commit 1**: Added network configuration support to admin helper service
**Commit 2**: Fixed queue directory path mismatch

Both changes are required for the network configuration feature to work properly.
