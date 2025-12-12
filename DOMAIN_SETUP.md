# Domain Setup Guide

This guide will help you connect your EC2 instance to your custom domain.

---

## Step 1: Configure DNS Records in Hostinger

### 1.1 Access Hostinger DNS Settings

1. Log in to your **domain registrar** account (e.g., Hostinger, GoDaddy, Namecheap)
2. Go to **Domains** → Select your root domain
3. Click on **DNS / Name Servers** or **DNS Zone Editor**

### 1.2 Add A Record

Add an **A Record** pointing to your EC2 Elastic IP:

| Type | Name/Host | Points To/Value | TTL |
|------|-----------|-----------------|-----|
| A    | `<subdomain>` | `<YOUR_EC2_ELASTIC_IP>` | 3600 (or Auto) |

**Important Notes:**
- **Name/Host**: Your subdomain name (e.g., `hrinterviewagent` or `app`) without the root domain
- **Points To**: Your EC2 Elastic IP address
- **TTL**: 3600 seconds (1 hour) or Auto

### 1.3 Verify DNS Propagation

Wait 5-15 minutes for DNS to propagate, then verify:

```bash
# From your local machine
nslookup <YOUR_DOMAIN>
# OR
dig <YOUR_DOMAIN>
```

You should see your EC2 Elastic IP address.

**Online DNS Checker:**
- Visit: https://dnschecker.org/
- Enter: `<YOUR_DOMAIN>`
- Check if it resolves to your EC2 Elastic IP globally

---

## Step 2: Update EC2 Security Group

### 2.1 Allow HTTP and HTTPS

1. Go to **AWS Console** → **EC2** → **Security Groups**
2. Select your instance's security group
3. **Edit Inbound Rules**:
   - **HTTP (80)**: Allow from `0.0.0.0/0`
   - **HTTPS (443)**: Allow from `0.0.0.0/0`
   - **SSH (22)**: Restrict to your IP only (for security)

---

## Step 3: Configure Nginx on EC2

### 3.1 SSH into Your EC2 Instance

```bash
ssh -i your-key.pem ubuntu@<YOUR_EC2_IP>
```

### 3.2 Install Nginx (if not already installed)

```bash
sudo apt-get update
sudo apt-get install -y nginx
```

### 3.3 Create Nginx Configuration

```bash
sudo nano /etc/nginx/sites-available/<YOUR_DOMAIN>
```

Add this configuration:

```nginx
server {
    listen 80;
    server_name <YOUR_DOMAIN>;

    # Logging
    access_log /var/log/nginx/hr-voice-agent-access.log;
    error_log /var/log/nginx/hr-voice-agent-error.log;

    # Increase timeouts for long-running requests
    proxy_read_timeout 300s;
    proxy_connect_timeout 75s;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        
        # Headers
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support (for voice interview)
        proxy_set_header Connection "upgrade";
        proxy_cache_bypass $http_upgrade;
        
        # Buffer settings
        proxy_buffering off;
        proxy_request_buffering off;
    }

    # Health check endpoint
    location /health {
        proxy_pass http://localhost:8000/health;
        access_log off;
    }
}
```

Save and exit (Ctrl+X, then Y, then Enter)

### 3.4 Enable the Site

```bash
# Create symbolic link
sudo ln -s /etc/nginx/sites-available/<YOUR_DOMAIN> /etc/nginx/sites-enabled/

# Remove default site (optional)
sudo rm /etc/nginx/sites-enabled/default

# Test configuration
sudo nginx -t
```

### 3.5 Start/Restart Nginx

```bash
sudo systemctl start nginx
sudo systemctl enable nginx
sudo systemctl reload nginx
```

### 3.6 Verify Nginx is Running

```bash
sudo systemctl status nginx
```

---

## Step 4: Set Up SSL/HTTPS with Let's Encrypt

### 4.1 Install Certbot

```bash
sudo apt-get update
sudo apt-get install -y certbot python3-certbot-nginx
```

### 4.2 Obtain SSL Certificate

```bash
sudo certbot --nginx -d <YOUR_DOMAIN>
```

**During the setup:**
- Enter your email address
- Agree to terms of service
- Choose whether to redirect HTTP to HTTPS (recommended: Yes)

### 4.3 Verify Certificate

Certbot automatically updates your Nginx configuration. Verify:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

### 4.4 Test SSL

Visit: `https://<YOUR_DOMAIN>`

You should see a secure connection with a padlock icon.

---

## Step 5: Auto-Renewal for SSL Certificate

Let's Encrypt certificates expire every 90 days. Set up auto-renewal:

### 5.1 Test Renewal

```bash
sudo certbot renew --dry-run
```

### 5.2 Certbot Auto-Renewal

Certbot automatically sets up a systemd timer. Verify it's active:

```bash
sudo systemctl status certbot.timer
```

If not active, enable it:

```bash
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer
```

---

## Step 6: Update Frontend API Configuration (if needed)

The frontend should automatically use the domain. Verify the API configuration:

```bash
# Check the API config file
cat ~/hr-voice-agent/frontend/src/config/api.ts
```

It should automatically detect production and use relative URLs (same domain).

---

## Step 7: Verify Everything Works

### 7.1 Test HTTP (should redirect to HTTPS)

```bash
curl -I http://<YOUR_DOMAIN>
```

Should return: `301 Moved Permanently` (redirect to HTTPS)

### 7.2 Test HTTPS

```bash
curl -I https://<YOUR_DOMAIN>
```

Should return: `200 OK`

### 7.3 Test Health Endpoint

```bash
curl https://<YOUR_DOMAIN>/health
```

Should return: `{"status":"healthy","service":"hr-voice-agent"}`

### 7.4 Access in Browser

Open: `https://<YOUR_DOMAIN>`

You should see your HR Voice Agent application!

---

## Step 8: Update CORS Settings (if needed)

If you encounter CORS errors, update the backend CORS settings:

```bash
# Edit the main.py file
nano ~/hr-voice-agent/backend/main.py
```

Find the CORS middleware section and update:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://<YOUR_DOMAIN>",
        "http://<YOUR_DOMAIN>",  # For redirects
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Then rebuild and restart the container:

```bash
cd ~/hr-voice-agent
docker stop hr-voice-agent
docker rm hr-voice-agent
docker build -t hr-voice-agent:latest .
docker run -d \
  --name hr-voice-agent \
  -p 8000:8000 \
  --env-file .env \
  -v ~/hr-voice-agent-data:/app/data \
  -v ~/qdrant-data:/app/qdrant_data \
  --restart unless-stopped \
  hr-voice-agent:latest
```

---

## Troubleshooting

### DNS Not Resolving

1. **Wait longer**: DNS can take up to 48 hours (usually 5-15 minutes)
2. **Check DNS records**: Verify A record is correct in Hostinger
3. **Clear DNS cache**: 
   ```bash
   # On Windows
   ipconfig /flushdns
   
   # On Mac/Linux
   sudo dscacheutil -flushcache
   ```

### Nginx Not Starting

```bash
# Check Nginx error logs
sudo tail -f /var/log/nginx/error.log

# Test configuration
sudo nginx -t

# Check if port 80/443 are in use
sudo netstat -tulpn | grep -E ':(80|443)'
```

### SSL Certificate Issues

```bash
# Check certificate status
sudo certbot certificates

# Renew manually
sudo certbot renew

# Check Certbot logs
sudo tail -f /var/log/letsencrypt/letsencrypt.log
```

### Application Not Accessible

1. **Check Docker container**:
   ```bash
   docker ps
   docker logs hr-voice-agent
   ```

2. **Check if app is running on port 8000**:
   ```bash
   curl http://localhost:8000/health
   ```

3. **Check Nginx proxy**:
   ```bash
   sudo tail -f /var/log/nginx/hr-voice-agent-error.log
   ```

### 502 Bad Gateway

This usually means Nginx can't connect to the backend:

1. **Check if container is running**:
   ```bash
   docker ps
   ```

2. **Check if port 8000 is listening**:
   ```bash
   sudo netstat -tulpn | grep 8000
   ```

3. **Restart container**:
   ```bash
   docker restart hr-voice-agent
   ```

---

## Security Recommendations

1. **Restrict SSH Access**: Only allow your IP in security group
2. **Enable Firewall**: Use `ufw` to restrict access
3. **Regular Updates**: Keep system and Docker updated
4. **Monitor Logs**: Set up log monitoring
5. **Backup Data**: Regularly backup your data volumes

---

## Quick Reference Commands

```bash
# Check DNS
nslookup <YOUR_DOMAIN>

# Test Nginx config
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx

# Check SSL certificate
sudo certbot certificates

# View Nginx logs
sudo tail -f /var/log/nginx/hr-voice-agent-error.log

# Check Docker container
docker logs -f hr-voice-agent

# Restart everything
sudo systemctl restart nginx
docker restart hr-voice-agent
```

---

## Summary

After completing these steps:

✅ DNS points to your EC2 instance  
✅ Nginx proxies requests to your app  
✅ SSL certificate installed and auto-renewing  
✅ Application accessible at `https://<YOUR_DOMAIN>`

Your HR Voice Agent is now live on your custom domain!

