#!/bin/bash
# Save to ~/ar25_maintenance_scripts/

# 1. Backup current config
sudo cp /etc/nginx/sites-enabled/ar25_config /etc/nginx/sites-enabled/ar25_config.bak_$(date +%Y%m%d)

# 2. Save process info
ps aux | grep gunicorn | grep ar25 > ~/ar25_process_snapshot_$(date +%Y%m%d).log

# 3. Save port bindings
sudo netstat -tulnp | grep -E '5000|8080' > ~/ar25_ports_$(date +%Y%m%d).log