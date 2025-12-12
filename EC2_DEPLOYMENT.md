# Step-by-Step EC2 Deployment Guide

This guide will walk you through deploying the HR Voice Agent application on an AWS EC2 instance.

## Prerequisites

- AWS Account
- AWS CLI installed and configured
- SSH key pair for EC2 access
- Basic knowledge of Linux commands

---

## Step 1: Launch an EC2 Instance

### 1.1 Create EC2 Instance

1. **Go to AWS Console** → EC2 → Launch Instance
2. **Configure Instance:**
   - **Name**: `hr-voice-agent`
   - **AMI**: Amazon Linux 2023 or Ubuntu 22.04 LTS (recommended)
   - **Instance Type**: `t3.medium` or larger (minimum 2 vCPU, 4GB RAM)
   - **Key Pair**: Select or create a new key pair (download `.pem` file)
   - **Network Settings**: 
     - Create or select a security group
     - Allow inbound traffic:
       - **SSH (22)** - from your IP
       - **HTTP (80)** - from anywhere (0.0.0.0/0)
       - **HTTPS (443)** - from anywhere (0.0.0.0/0)
       - **Custom TCP (8000)** - from anywhere (for testing, restrict later)
   - **Storage**: 20GB minimum (30GB recommended for Docker images and data)
   - **Advanced Details** (optional): Add user data script (see Step 1.2)

### 1.2 (Optional) User Data Script for Auto-Setup

You can add this script in "Advanced Details" → "User data" to automatically install Docker:

```bash
#!/bin/bash
# For Amazon Linux 2023
yum update -y
yum install -y docker
systemctl start docker
systemctl enable docker
usermod -a -G docker ec2-user

# For Ubuntu 22.04
# apt-get update
# apt-get install -y docker.io
# systemctl start docker
# systemctl enable docker
# usermod -a -G docker ubuntu
```

3. **Launch Instance** and wait for it to be running

---

## Step 2: Connect to EC2 Instance

### 2.1 Get Instance Public IP

1. Go to EC2 → Instances
2. Select your instance
3. Copy the **Public IPv4 address**

### 2.2 SSH into Instance

**For Amazon Linux:**
```bash
ssh -i your-key.pem ec2-user@<PUBLIC_IP>
```

**For Ubuntu:**
```bash
ssh -i your-key.pem ubuntu@<PUBLIC_IP>
```

**Note**: If you get permission denied, fix key permissions:
```bash
chmod 400 your-key.pem
```

---

## Step 3: Install Docker (if not using user data)

### 3.1 For Amazon Linux 2023

```bash
sudo yum update -y
sudo yum install -y docker
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -a -G docker ec2-user
```

**Log out and log back in** for group changes to take effect.

### 3.2 For Ubuntu 22.04

```bash
sudo apt-get update
sudo apt-get install -y docker.io
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -a -G docker ubuntu
```

**Log out and log back in** for group changes to take effect.

### 3.3 Verify Docker Installation

```bash
docker --version
docker ps
```

---

## Step 4: Install Docker Compose (Optional but Recommended)

```bash
# For Amazon Linux
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# For Ubuntu
sudo apt-get install -y docker-compose
```

---

## Step 5: Clone Your Repository

### 5.1 Install Git

**Amazon Linux:**
```bash
sudo yum install -y git
```

**Ubuntu:**
```bash
sudo apt-get install -y git
```

### 5.2 Set Up GitHub Authentication

GitHub no longer supports password authentication. You have two options:

#### Option A: Use SSH Keys (Recommended)

**Step 1: Generate SSH Key on EC2**
```bash
ssh-keygen -t ed25519 -C "your-email@example.com"
# Press Enter to accept default location (~/.ssh/id_ed25519)
# Press Enter twice for no passphrase (or set one if preferred)
```

**Step 2: Display Public Key**
```bash
cat ~/.ssh/id_ed25519.pub
```

**Step 3: Add SSH Key to GitHub**
1. Copy the output from Step 2
2. Go to GitHub → Settings → SSH and GPG keys
3. Click "New SSH key"
4. Paste the key and save

**Step 4: Clone Using SSH**
```bash
cd ~
git clone git@github.com:techleadershub/hr-voice-agent.git
cd hr-voice-agent
```

#### Option B: Use Personal Access Token (PAT)

**Step 1: Create Personal Access Token**
1. Go to GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click "Generate new token (classic)"
3. Give it a name (e.g., "EC2 Deployment")
4. Select scopes: `repo` (full control of private repositories)
5. Click "Generate token"
6. **Copy the token immediately** (you won't see it again!)

**Step 2: Clone Using Token**
```bash
cd ~
git clone https://<YOUR_TOKEN>@github.com/techleadershub/hr-voice-agent.git
cd hr-voice-agent
```

**OR** use your username:
```bash
git clone https://techleadershub:<YOUR_TOKEN>@github.com/techleadershub/hr-voice-agent.git
```

**Note**: Replace `<YOUR_TOKEN>` with your actual token.

### 5.3 Alternative: Upload Files Directly

**OR** if you want to upload files directly:

```bash
# Create project directory
mkdir -p ~/hr-voice-agent
cd ~/hr-voice-agent
```

Then use `scp` from your local machine:
```bash
# From your local machine
scp -i your-key.pem -r hr-voice-agent ubuntu@<PUBLIC_IP>:~/
```

---

## Step 6: Set Up Environment Variables

### 6.1 Create .env File

```bash
cd ~/hr-voice-agent
nano .env
```

Add the following (replace with your actual values):

```env
OPENAI_API_KEY=sk-your-actual-openai-api-key-here
QDRANT_URL=
QDRANT_API_KEY=
```

**Note about optional variables:**
- `PYTHONPATH=/app` - **Optional**: Already set in Dockerfile, but you can include it if you want to override
- `DATA_DIR=/app/data` - **Not necessary**: The code doesn't actually use this variable (it uses hardcoded paths)

**Minimum required .env file:**
```env
OPENAI_API_KEY=sk-your-actual-openai-api-key-here
```

**Optional (if using external Qdrant):**
```env
QDRANT_URL=https://your-qdrant-instance.com
QDRANT_API_KEY=your-qdrant-api-key
```

Save and exit (Ctrl+X, then Y, then Enter)

### 6.2 Secure the .env File

```bash
chmod 600 .env
```

---

## Step 7: Build Docker Image

### 7.1 Build the Image

```bash
cd ~/hr-voice-agent
docker build -t hr-voice-agent:latest .
```

**Note**: This will take 5-10 minutes as it:
- Builds the frontend
- Installs Python dependencies
- Downloads ML models (sentence-transformers)

### 7.2 Verify Image

```bash
docker images | grep hr-voice-agent
```

---

## Step 8: Run the Container

### 8.1 Create Data Directories

```bash
mkdir -p ~/hr-voice-agent-data
mkdir -p ~/qdrant-data
```

### 8.2 Run Container

```bash
docker run -d \
  --name hr-voice-agent \
  -p 8000:8000 \
  --env-file .env \
  -v ~/hr-voice-agent-data:/app/data \
  -v ~/qdrant-data:/app/qdrant_data \
  --restart unless-stopped \
  hr-voice-agent:latest
```

**Explanation:**
- `-d`: Run in detached mode (background)
- `--name`: Container name
- `-p 8000:8000`: Map port 8000
- `--env-file .env`: Load environment variables
- `-v`: Mount volumes for persistent data
- `--restart unless-stopped`: Auto-restart on reboot

### 8.3 Check Container Status

```bash
docker ps
docker logs hr-voice-agent
```

---

## Step 9: Configure Security Group

### 9.1 Update Security Group Rules

1. Go to EC2 → Security Groups
2. Select your instance's security group
3. **Edit Inbound Rules:**
   - **HTTP (80)**: Allow from anywhere (0.0.0.0/0)
   - **HTTPS (443)**: Allow from anywhere (0.0.0.0/0)
   - **Custom TCP (8000)**: Allow from anywhere (for testing)

**For Production**: Restrict port 8000 to specific IPs or use a load balancer.

---

## Step 10: Test the Application

### 10.1 Check Health Endpoint

```bash
curl http://localhost:8000/health
```

Should return: `{"status":"healthy","service":"hr-voice-agent"}`

### 10.2 Access from Browser

Open in your browser:
```
http://<EC2_PUBLIC_IP>:8000
```

You should see the HR Voice Agent interface.

---

## Step 11: Set Up Nginx Reverse Proxy (Recommended)

### 11.1 Install Nginx

**Amazon Linux:**
```bash
sudo yum install -y nginx
```

**Ubuntu:**
```bash
sudo apt-get install -y nginx
```

### 11.2 Configure Nginx

```bash
sudo nano /etc/nginx/conf.d/hr-voice-agent.conf
```

Add this configuration:

```nginx
server {
    listen 80;
    server_name _;  # Replace with your domain name if you have one

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # WebSocket support
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;
    }
}
```

### 11.3 Start Nginx

```bash
sudo systemctl start nginx
sudo systemctl enable nginx
sudo nginx -t  # Test configuration
sudo systemctl reload nginx
```

### 11.4 Access via Port 80

Now you can access the app at:
```
http://<EC2_PUBLIC_IP>
```

---

## Step 12: Set Up SSL/HTTPS (Optional but Recommended)

### 12.1 Install Certbot

**Amazon Linux:**
```bash
sudo yum install -y certbot python3-certbot-nginx
```

**Ubuntu:**
```bash
sudo apt-get install -y certbot python3-certbot-nginx
```

### 12.2 Get SSL Certificate

```bash
sudo certbot --nginx -d your-domain.com
```

**Note**: You need a domain name pointing to your EC2 instance for this to work.

---

## Step 13: Set Up Auto-Start on Reboot

### 13.1 Create Systemd Service (Optional)

```bash
sudo nano /etc/systemd/system/hr-voice-agent.service
```

Add:

```ini
[Unit]
Description=HR Voice Agent Docker Container
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/ubuntu/hr-voice-agent
ExecStart=/usr/bin/docker start hr-voice-agent
ExecStop=/usr/bin/docker stop hr-voice-agent
User=ec2-user

[Install]
WantedBy=multi-user.target
```

Enable service:
```bash
sudo systemctl enable hr-voice-agent
sudo systemctl start hr-voice-agent
```

---

## Step 14: Monitoring and Logs

### 14.1 View Container Logs

```bash
docker logs hr-voice-agent
docker logs -f hr-voice-agent  # Follow logs
```

### 14.2 Check Container Status

```bash
docker ps -a
docker stats hr-voice-agent
```

### 14.3 Check System Resources

```bash
free -h
df -h
top
```

---

## Step 15: Update Application

### 15.1 Pull Latest Code

```bash
cd ~/hr-voice-agent
git pull
```

### 15.2 Rebuild and Restart

```bash
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

### Container Won't Start

```bash
# Check logs
docker logs hr-voice-agent

# Check if port is in use
sudo netstat -tulpn | grep 8000

# Check Docker status
sudo systemctl status docker
```

### Out of Memory

- Increase instance size (t3.medium → t3.large)
- Or add swap space:
```bash
sudo dd if=/dev/zero of=/swapfile bs=1G count=2
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### Can't Access from Browser

1. Check security group rules
2. Check if container is running: `docker ps`
3. Check if port is listening: `sudo netstat -tulpn | grep 8000`
4. Check firewall: `sudo iptables -L`

### Database/Data Persistence

Data is stored in mounted volumes:
- `~/hr-voice-agent-data` - SQLite database
- `~/qdrant-data` - Qdrant vector store

To backup:
```bash
tar -czf backup-$(date +%Y%m%d).tar.gz ~/hr-voice-agent-data ~/qdrant-data
```

---

## Security Best Practices

1. **Restrict SSH Access**: Only allow your IP in security group
2. **Use HTTPS**: Set up SSL certificate
3. **Update Regularly**: `sudo yum update` or `sudo apt-get update`
4. **Firewall**: Configure iptables or use AWS Security Groups
5. **Environment Variables**: Never commit `.env` file
6. **Regular Backups**: Backup data volumes regularly

---

## Cost Optimization

- **Instance Type**: Start with t3.medium, scale as needed
- **Storage**: Use gp3 volumes (cheaper than gp2)
- **Reserved Instances**: For long-term use, consider Reserved Instances
- **Stop When Not in Use**: Stop instance when not needed

---

## Next Steps

1. Set up domain name and DNS
2. Configure CloudWatch for monitoring
3. Set up automated backups
4. Consider using RDS for database (instead of SQLite)
5. Set up external Qdrant instance for production
6. Configure auto-scaling if needed

---

## Quick Reference Commands

```bash
# Start container
docker start hr-voice-agent

# Stop container
docker stop hr-voice-agent

# View logs
docker logs -f hr-voice-agent

# Restart container
docker restart hr-voice-agent

# Check status
docker ps -a

# Access container shell
docker exec -it hr-voice-agent /bin/bash

# Rebuild image
docker build -t hr-voice-agent:latest .
```

---

## Support

If you encounter issues:
1. Check Docker logs: `docker logs hr-voice-agent`
2. Check Nginx logs: `sudo tail -f /var/log/nginx/error.log`
3. Check system logs: `sudo journalctl -u docker`
4. Verify environment variables: `docker exec hr-voice-agent env`

