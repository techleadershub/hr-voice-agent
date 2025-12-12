#!/bin/bash
# EC2 Setup Script for HR Voice Agent
# Run this script on your EC2 instance after connecting via SSH

set -e

echo "=========================================="
echo "HR Voice Agent - EC2 Setup Script"
echo "=========================================="

# Detect OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
else
    echo "Cannot detect OS. Exiting."
    exit 1
fi

echo "Detected OS: $OS"

# Install Docker
echo ""
echo "Step 1: Installing Docker..."
if [ "$OS" = "amzn" ] || [ "$OS" = "rhel" ]; then
    # Amazon Linux
    sudo yum update -y
    sudo yum install -y docker
    sudo systemctl start docker
    sudo systemctl enable docker
    sudo usermod -a -G docker ec2-user
    echo "Docker installed for Amazon Linux"
elif [ "$OS" = "ubuntu" ] || [ "$OS" = "debian" ]; then
    # Ubuntu/Debian
    sudo apt-get update
    sudo apt-get install -y docker.io
    sudo systemctl start docker
    sudo systemctl enable docker
    sudo usermod -a -G docker ubuntu
    echo "Docker installed for Ubuntu"
else
    echo "Unsupported OS. Please install Docker manually."
    exit 1
fi

# Install Docker Compose
echo ""
echo "Step 2: Installing Docker Compose..."
if [ "$OS" = "amzn" ] || [ "$OS" = "rhel" ]; then
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
elif [ "$OS" = "ubuntu" ] || [ "$OS" = "debian" ]; then
    sudo apt-get install -y docker-compose
fi

# Install Git
echo ""
echo "Step 3: Installing Git..."
if [ "$OS" = "amzn" ] || [ "$OS" = "rhel" ]; then
    sudo yum install -y git
elif [ "$OS" = "ubuntu" ] || [ "$OS" = "debian" ]; then
    sudo apt-get install -y git
fi

# Install Nginx (optional)
echo ""
read -p "Do you want to install Nginx? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Step 4: Installing Nginx..."
    if [ "$OS" = "amzn" ] || [ "$OS" = "rhel" ]; then
        sudo yum install -y nginx
    elif [ "$OS" = "ubuntu" ] || [ "$OS" = "debian" ]; then
        sudo apt-get install -y nginx
    fi
    echo "Nginx installed. Configuration will be done manually."
fi

# Create directories
echo ""
echo "Step 5: Creating data directories..."
mkdir -p ~/hr-voice-agent-data
mkdir -p ~/qdrant-data
echo "Directories created:"
echo "  - ~/hr-voice-agent-data"
echo "  - ~/qdrant-data"

# Verify installations
echo ""
echo "Step 6: Verifying installations..."
docker --version
docker-compose --version
git --version

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Log out and log back in for Docker group changes to take effect"
echo "2. Clone your repository: git clone <your-repo-url>"
echo "3. Create .env file with your OPENAI_API_KEY"
echo "4. Build Docker image: docker build -t hr-voice-agent:latest ."
echo "5. Run container: docker run -d --name hr-voice-agent -p 8000:8000 --env-file .env -v ~/hr-voice-agent-data:/app/data -v ~/qdrant-data:/app/qdrant_data --restart unless-stopped hr-voice-agent:latest"
echo ""
echo "For detailed instructions, see EC2_DEPLOYMENT.md"

