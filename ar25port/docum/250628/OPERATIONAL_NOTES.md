# AR25 Working Configuration
Last verified working: Sat Jun 28 11:40:25 PM UTC 2025

## Key Components
- Nginx config: /etc/nginx/conf.d/default.conf
- Gunicorn command: gunicorn -b 127.0.0.1:5000 main:app
- Port: 5000
- Virtualenv: ~/ar25port/venv

## Recovery Steps
1. Restart Gunicorn:
   cd ~/ar25port && source venv/bin/activate
   pkill gunicorn
   gunicorn -b 127.0.0.1:5000 main:app

2. Restart Nginx:
   sudo systemctl restart nginx
