#!/bin/bash
# Domain Setup Script
# Run this on your EC2 instance after DNS is configured
# Usage: sudo ./setup-domain.sh <your-domain.com>

set -e

if [ -z "$1" ]; then
    echo "Usage: sudo ./setup-domain.sh <your-domain.com>"
    echo "Example: sudo ./setup-domain.sh app.yourdomain.com"
    exit 1
fi

DOMAIN="$1"
APP_PORT=8000

echo "=========================================="
echo "Domain Setup: $DOMAIN"
echo "=========================================="

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then 
    echo "Please run with sudo"
    exit 1
fi

# Install Nginx if not installed
if ! command -v nginx &> /dev/null; then
    echo "Installing Nginx..."
    apt-get update
    apt-get install -y nginx
fi

# Create Nginx configuration
echo ""
echo "Creating Nginx configuration..."
cat > /etc/nginx/sites-available/$DOMAIN <<EOF
server {
    listen 80;
    server_name $DOMAIN;

    # Logging
    access_log /var/log/nginx/hr-voice-agent-access.log;
    error_log /var/log/nginx/hr-voice-agent-error.log;

    # Increase timeouts for long-running requests
    proxy_read_timeout 300s;
    proxy_connect_timeout 75s;

    location / {
        proxy_pass http://localhost:$APP_PORT;
        proxy_http_version 1.1;
        
        # Headers
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # WebSocket support (for voice interview)
        proxy_set_header Connection "upgrade";
        proxy_cache_bypass \$http_upgrade;
        
        # Buffer settings
        proxy_buffering off;
        proxy_request_buffering off;
    }

    # Health check endpoint
    location /health {
        proxy_pass http://localhost:$APP_PORT/health;
        access_log off;
    }
}
EOF

# Enable site
echo "Enabling site..."
ln -sf /etc/nginx/sites-available/$DOMAIN /etc/nginx/sites-enabled/

# Remove default site if exists
if [ -f /etc/nginx/sites-enabled/default ]; then
    rm /etc/nginx/sites-enabled/default
fi

# Test configuration
echo ""
echo "Testing Nginx configuration..."
nginx -t

# Start/Reload Nginx
echo ""
echo "Starting Nginx..."
systemctl start nginx
systemctl enable nginx
systemctl reload nginx

echo ""
echo "=========================================="
echo "Nginx configured successfully!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Verify DNS is pointing to your EC2 IP:"
echo "   nslookup $DOMAIN"
echo ""
echo "2. Install SSL certificate:"
echo "   sudo apt-get install -y certbot python3-certbot-nginx"
echo "   sudo certbot --nginx -d $DOMAIN"
echo ""
echo "3. Test your site:"
echo "   curl http://$DOMAIN/health"
echo ""

