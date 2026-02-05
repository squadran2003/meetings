#!/bin/bash
# AWS Lightsail Setup Script for Video Conferencing App
# Run this on a fresh Ubuntu 22.04 Lightsail instance

set -e

echo "=== Video Conferencing App - Lightsail Setup ==="

# Update system
echo "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install Docker
echo "Installing Docker..."
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
sudo usermod -aG docker $USER

# Install nginx
echo "Installing nginx..."
sudo apt install -y nginx

# Install certbot for SSL
echo "Installing certbot..."
sudo apt install -y certbot python3-certbot-nginx

# Install Node.js for building frontend
echo "Installing Node.js..."
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Create app directory
echo "Setting up application directory..."
sudo mkdir -p /opt/meetings
sudo chown $USER:$USER /opt/meetings

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "1. Clone your repo to /opt/meetings"
echo "2. Build the frontend: cd /opt/meetings/frontend && npm install && npm run build"
echo "3. Copy frontend build to backend: cp -r /opt/meetings/frontend/dist /opt/meetings/backend/static"
echo "4. Start the backend: cd /opt/meetings && docker compose -f docker-compose.prod.yml up -d"
echo "5. Configure nginx (see below)"
echo "6. Get SSL certificate: sudo certbot --nginx -d yourdomain.com"
echo ""
echo "=== Nginx Configuration ==="
echo "Create /etc/nginx/sites-available/meetings with:"
echo ""
cat << 'NGINX'
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
}
NGINX
echo ""
echo "Then run:"
echo "  sudo ln -s /etc/nginx/sites-available/meetings /etc/nginx/sites-enabled/"
echo "  sudo nginx -t && sudo systemctl reload nginx"
echo "  sudo certbot --nginx -d yourdomain.com"
