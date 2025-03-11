# ChatterBox Deployment Guide

## Prerequisites

- Python 3.8+
- PostgreSQL
- Redis
- Domain name (for production)
- SSL certificate (for production)

## Environment Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd chatterbox
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
- Copy `.env.example` to `.env`
- Update the values in `.env` with your production settings

## Database Setup

1. Create a PostgreSQL database:
```sql
CREATE DATABASE chatterbox;
```

2. Run migrations:
```bash
python manage.py migrate
```

3. Create a superuser:
```bash
python manage.py createsuperuser
```

## Static Files

1. Collect static files:
```bash
python manage.py collectstatic
```

## Redis Setup

1. Install Redis server
2. Ensure Redis is running on the configured host/port
3. Test Redis connection:
```bash
redis-cli ping
```

## SSL Setup

1. Obtain SSL certificate for your domain
2. Configure your web server (Nginx/Apache) with SSL

## Server Configuration (Nginx Example)

```nginx
upstream chatterbox {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://chatterbox;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /path/to/staticfiles/;
    }

    location /media/ {
        alias /path/to/mediafiles/;
    }
}
```

## Running the Application

1. Start the ASGI server:
```bash
daphne chatterbox.asgi:application -b 0.0.0.0 -p 8000
```

2. Start the background task worker:
```bash
python manage.py process_tasks
```

## Monitoring

1. Check application logs:
```bash
tail -f logs/django.log
```

2. Monitor Redis:
```bash
redis-cli monitor
```

## Maintenance

1. Database backups:
```bash
pg_dump chatterbox > backup.sql
```

2. Update application:
```bash
git pull
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic
systemctl restart chatterbox
```

## Security Checklist

- [ ] Debug mode is disabled
- [ ] Secret key is properly set
- [ ] Database credentials are secure
- [ ] SSL is properly configured
- [ ] File permissions are set correctly
- [ ] Firewall rules are configured
- [ ] Regular security updates are scheduled
- [ ] Backup system is in place

## Troubleshooting

1. Check logs in `logs/django.log`
2. Verify Redis connection
3. Check database connectivity
4. Verify static files are served correctly
5. Check SSL certificate validity

For additional support, please refer to the project documentation or create an issue in the repository. 