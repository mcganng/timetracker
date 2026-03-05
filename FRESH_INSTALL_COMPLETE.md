# Fresh Install - Complete Fix

## Problem on Fresh Installs

When installing Time Tracker from a fresh git clone, the server configuration features (timezone, network, NTP) were failing with:

```
Error: Failed to communicate with admin helper: [Errno 30] Read-only file system
```

## Root Causes - Three Separate Issues

### Issue 1: Network Configuration Not Implemented
Admin helper service only supported timezone/NTP - no network support.

### Issue 2: Queue Directory Path Mismatch  
- Service monitored: `/var/run/timetracker/`
- Client wrote to: `/opt/timetracker/queue/`

### Issue 3: Client Trying to Create Directories
Client tried to create `/var/run/timetracker/` but timetracker user lacks permission.
This caused "Read-only file system" errors.

## Solution Applied

All three issues have been fixed in the latest git commit.

## For Fresh Installs - Run install.sh

```bash
cd /opt/timetracker
sudo bash install.sh
```

The installer now handles everything automatically.

## For Existing Installs - Update Script

```bash
cd /opt/timetracker
sudo git pull
sudo /opt/timetracker/update_from_git.sh
```

## Testing

After installation, test all three features:

1. **Timezone**: Admin → Server Config → Time & NTP → Change timezone
2. **Network**: Admin → Server Config → Network → Modify network settings  
3. **NTP**: Admin → Server Config → Time & NTP → Update NTP servers

All should show success messages.

## Troubleshooting

View logs if issues occur:
```bash
sudo journalctl -u timetracker-admin-helper -f
sudo journalctl -u timetracker -f
```

You should see "Processing request" and "Successfully set..." messages.

