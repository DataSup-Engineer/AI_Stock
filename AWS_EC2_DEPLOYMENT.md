# AWS EC2 Deployment Guide - NASDAQ Stock Agent

Complete step-by-step guide to deploy the NASDAQ Stock Agent on AWS EC2 using Docker.

## 📋 Prerequisites

- AWS account with EC2 access
- SSH key pair for EC2 access
- Anthropic API key ([Get one here](https://console.anthropic.com/))
- Basic knowledge of SSH and command line

## 🚀 Part 1: Launch EC2 Instance

### Step 1: Login to AWS Console

1. Go to [AWS Console](https://console.aws.amazon.com/)
2. Navigate to **EC2 Dashboard**
3. Click **Launch Instance**

### Step 2: Configure Instance

**Basic Details:**
- **Name**: `nasdaq-stock-agent`
- **Application and OS Images (AMI)**: Ubuntu Server 22.04 LTS
- **Architecture**: 64-bit (x86)

**Instance Type:**
- **Type**: `t3.medium`
- **vCPU**: 2
- **Memory**: 4 GiB
- **Why**: Minimum requirements for running the agent with MongoDB

**Key Pair:**
- Select existing key pair OR
- Click **Create new key pair**
  - Name: `nasdaq-agent-key`
  - Type: RSA
  - Format: .pem (for Mac/Linux) or .ppk (for Windows)
  - Download and save securely

**Network Settings:**
- Click **Edit** next to Network settings
- **Create security group**: Yes
- **Security group name**: `nasdaq-agent-sg`

**Inbound Security Rules:**

| Type | Protocol | Port | Source | Description |
|------|----------|------|--------|-------------|
| SSH | TCP | 22 | My IP | SSH access |
| HTTP | TCP | 80 | 0.0.0.0/0 | HTTP access |
| HTTPS | TCP | 443 | 0.0.0.0/0 | HTTPS access |
| Custom TCP | TCP | 8000 | 0.0.0.0/0 | FastAPI |
| Custom TCP | TCP | 6000 | 0.0.0.0/0 | NEST A2A |

**Storage:**
- **Size**: 20 GiB
- **Volume Type**: gp3 (General Purpose SSD)

### Step 3: Launch Instance

1. Review all settings
2. Click **Launch Instance**
3. Wait for instance to start (Status: Running)
4. Note down:
   - **Instance ID**: `i-xxxxxxxxxxxxx`
   - **Public IPv4 address**: `xx.xx.xx.xx`

## 🔌 Part 2: Connect to EC2 Instance

### Step 1: Set Key Permissions (Local Machine)

```bash
# Navigate to where you saved the key
cd ~/Downloads

# Set correct permissions
chmod 400 nasdaq-agent-key.pem
```

### Step 2: Connect via SSH

```bash
# Replace with your actual public IP
ssh -i nasdaq-agent-key.pem ubuntu@YOUR_EC2_PUBLIC_IP

# Example:
# ssh -i nasdaq-agent-key.pem ubuntu@54.123.45.67
```

**First time connection:**
- You'll see: "Are you sure you want to continue connecting?"
- Type: `yes` and press Enter

**You're now connected to your EC2 instance!** ✅

## 🐳 Part 3: Install Docker

### Step 1: Update System

```bash
# Update package list
sudo apt-get update

# Upgrade installed packages
sudo apt-get upgrade -y
```

### Step 2: Install Docker

```bash
# Download Docker installation script
curl -fsSL https://get.docker.com -o get-docker.sh

# Run installation script
sudo sh get-docker.sh

# Add current user to docker group (no sudo needed)
sudo usermod -aG docker ubuntu

# Apply group changes
newgrp docker

# Verify Docker installation
docker --version
```

**Expected output:** `Docker version 24.x.x, build xxxxxxx`

### Step 3: Install Docker Compose

```bash
# Download Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

# Make it executable
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker-compose --version
```

**Expected output:** `Docker Compose version v2.x.x`

## 📦 Part 4: Deploy Application

### Step 1: Clone Repository

```bash
# Clone from GitHub
git clone https://github.com/YOUR_USERNAME/nasdaq-stock-agent.git

# Navigate to project directory
cd nasdaq-stock-agent
```

### Step 2: Configure Environment

```bash
# Create .env from template
cp .env.example .env

# Edit .env file
nano .env
```

**Update these values in .env:**

```bash
# REQUIRED: Add your Anthropic API key
ANTHROPIC_API_KEY=your_actual_anthropic_api_key_here

# REQUIRED: Set secure MongoDB passwords
MONGO_ROOT_PASSWORD=your_secure_root_password_here
MONGO_PASSWORD=your_secure_user_password_here

# OPTIONAL: NEST will be auto-configured by startup script
# But you can set it manually if needed
# NEST_ENABLED=true
# NEST_PUBLIC_URL=http://YOUR_EC2_PUBLIC_IP:6000
```

**Save and exit:**
- Press `Ctrl + X`
- Press `Y` to confirm
- Press `Enter` to save

### Step 3: Deploy with Automatic IP Detection

**Option A: Quick Deploy (Recommended)**

```bash
# One command to deploy everything
./quick-deploy.sh
```

This will:
1. Verify .env configuration
2. Automatically detect your EC2 public IP
3. Update NEST_PUBLIC_URL
4. Start all services in production mode

**Option B: Manual Deployment**

```bash
# Run startup script
./startup.sh prod

# Or start services manually
docker-compose -f docker-compose.prod.yml up -d
```

### Step 4: Verify Deployment

```bash
# Check if containers are running
docker-compose -f docker-compose.prod.yml ps

# You should see:
# - nasdaq-agent-mongodb-prod (healthy)
# - nasdaq-stock-agent-prod (healthy)
# - nasdaq-agent-nginx (healthy)
```

## ✅ Part 5: Test Your Agent

### Test 1: Health Check

```bash
# Test locally on EC2
curl http://localhost:8000/

# Expected: JSON response with service info
```

### Test 2: From Your Local Machine

```bash
# Replace with your EC2 public IP
curl http://YOUR_EC2_PUBLIC_IP:8000/

# Test stock analysis
curl -X POST http://YOUR_EC2_PUBLIC_IP:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{"query": "AAPL"}'
```

### Test 3: Access API Documentation

Open in your browser:
```
http://YOUR_EC2_PUBLIC_IP:8000/docs
```

You should see the interactive Swagger UI documentation.

### Test 4: Verify NEST Registration (if enabled)

```bash
# Check if registered with NANDA
curl http://registry.chat39.com:6900/agents/nasdaq-stock-agent

# View agent logs
docker-compose -f docker-compose.prod.yml logs nasdaq-agent | grep -i nest
```

## 📊 Part 6: Monitor Your Agent

### View Logs

```bash
# All services
docker-compose -f docker-compose.prod.yml logs -f

# Specific service
docker-compose -f docker-compose.prod.yml logs -f nasdaq-agent

# Last 100 lines
docker-compose -f docker-compose.prod.yml logs --tail=100 nasdaq-agent

# Exit logs: Press Ctrl+C
```

### Check Service Status

```bash
# Container status
docker-compose -f docker-compose.prod.yml ps

# Resource usage
docker stats

# Disk usage
df -h
```

### Check System Resources

```bash
# Memory usage
free -h

# CPU usage
top
# Press 'q' to exit
```

## 🔧 Part 7: Manage Your Agent

### Restart Services

```bash
# Restart all services
docker-compose -f docker-compose.prod.yml restart

# Restart specific service
docker-compose -f docker-compose.prod.yml restart nasdaq-agent
```

### Stop Services

```bash
# Stop all services
docker-compose -f docker-compose.prod.yml down

# Stop and remove volumes (WARNING: deletes data)
docker-compose -f docker-compose.prod.yml down -v
```

### Update Application

```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d --build
```

### Backup MongoDB Data

```bash
# Create backup
docker exec nasdaq-agent-mongodb-prod mongodump --out=/data/backup

# Copy to host
docker cp nasdaq-agent-mongodb-prod:/data/backup ./mongodb-backup-$(date +%Y%m%d)

# Download to local machine (from your local terminal)
scp -i nasdaq-agent-key.pem -r ubuntu@YOUR_EC2_IP:~/nasdaq-stock-agent/mongodb-backup-* ./
```

## 🆘 Part 8: Troubleshooting

### Agent Won't Start

```bash
# Check logs for errors
docker-compose -f docker-compose.prod.yml logs nasdaq-agent

# Check if API key is set
docker exec nasdaq-stock-agent-prod env | grep ANTHROPIC

# Restart the agent
docker-compose -f docker-compose.prod.yml restart nasdaq-agent
```

### MongoDB Connection Issues

```bash
# Check MongoDB status
docker-compose -f docker-compose.prod.yml ps mongodb

# Check MongoDB logs
docker-compose -f docker-compose.prod.yml logs mongodb

# Test MongoDB connection
docker exec -it nasdaq-agent-mongodb-prod mongosh -u admin -p
```

### Port Already in Use

```bash
# Check what's using the port
sudo netstat -tulpn | grep 8000

# Kill the process (if needed)
sudo kill -9 <PID>
```

### Out of Memory

```bash
# Check memory
free -h

# Add swap space (2GB)
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Make permanent
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### Can't Access from Browser

1. **Check Security Group:**
   - Go to EC2 Console
   - Select your instance
   - Click Security tab
   - Verify port 8000 is open to 0.0.0.0/0

2. **Check if service is running:**
   ```bash
   docker-compose -f docker-compose.prod.yml ps
   curl http://localhost:8000/
   ```

3. **Check firewall:**
   ```bash
   sudo ufw status
   # If active, allow ports
   sudo ufw allow 8000/tcp
   sudo ufw allow 6000/tcp
   ```

### NEST Registration Failed

```bash
# Check NEST configuration
grep NEST_ .env

# Verify public URL is correct
curl http://169.254.169.254/latest/meta-data/public-ipv4

# Re-run startup script to update IP
./startup.sh prod

# Check registry connectivity
curl http://registry.chat39.com:6900/health
```

## 🔐 Part 9: Security Best Practices

### 1. Restrict SSH Access

```bash
# In AWS Console:
# EC2 > Security Groups > nasdaq-agent-sg
# Edit inbound rules for SSH (port 22)
# Change source from 0.0.0.0/0 to "My IP"
```

### 2. Setup Firewall

```bash
# Install UFW
sudo apt-get install ufw -y

# Configure firewall
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 8000/tcp  # FastAPI
sudo ufw allow 6000/tcp  # NEST

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

### 3. Enable Automatic Updates

```bash
# Install unattended-upgrades
sudo apt-get install unattended-upgrades -y

# Enable automatic updates
sudo dpkg-reconfigure -plow unattended-upgrades
```

### 4. Change Default Passwords

Make sure you changed these in `.env`:
- `MONGO_ROOT_PASSWORD`
- `MONGO_PASSWORD`

### 5. Regular Backups

Set up a cron job for automatic backups:

```bash
# Edit crontab
crontab -e

# Add daily backup at 2 AM
0 2 * * * cd ~/nasdaq-stock-agent && docker exec nasdaq-agent-mongodb-prod mongodump --out=/data/backup-$(date +\%Y\%m\%d)
```

## 📈 Part 10: Performance Optimization

### Monitor Resource Usage

```bash
# Install htop for better monitoring
sudo apt-get install htop -y

# Run htop
htop
```

### Optimize Docker

```bash
# Clean up unused Docker resources
docker system prune -a

# Remove old images
docker image prune -a
```

### Increase Instance Size (if needed)

If your agent is slow:
1. Stop the instance
2. Change instance type to `t3.large` (4 vCPU, 8 GiB)
3. Start the instance
4. Reconnect and restart services

## 🎯 Quick Reference Commands

```bash
# Start services
docker-compose -f docker-compose.prod.yml up -d

# Stop services
docker-compose -f docker-compose.prod.yml down

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Restart services
docker-compose -f docker-compose.prod.yml restart

# Check status
docker-compose -f docker-compose.prod.yml ps

# Update and restart
git pull && docker-compose -f docker-compose.prod.yml up -d --build

# Backup MongoDB
docker exec nasdaq-agent-mongodb-prod mongodump --out=/data/backup

# Get public IP
curl http://169.254.169.254/latest/meta-data/public-ipv4

# Update NEST URL
./startup.sh prod
```

## 📞 Support

- **API Documentation**: `http://YOUR_EC2_IP:8000/docs`
- **Check Logs**: `docker-compose -f docker-compose.prod.yml logs -f`
- **GitHub Issues**: Open an issue in your repository

## ✅ Deployment Checklist

- [ ] EC2 instance launched (t3.medium, Ubuntu 22.04)
- [ ] Security group configured (ports 22, 80, 443, 8000, 6000)
- [ ] SSH connection working
- [ ] Docker installed and verified
- [ ] Docker Compose installed and verified
- [ ] Repository cloned
- [ ] .env file created and configured
- [ ] ANTHROPIC_API_KEY added
- [ ] MongoDB passwords set
- [ ] Services started successfully
- [ ] Health check passing (http://YOUR_IP:8000/)
- [ ] API documentation accessible
- [ ] NEST registration verified (if enabled)
- [ ] Firewall configured
- [ ] Automatic updates enabled
- [ ] Backup strategy in place

## 🎉 Success!

Your NASDAQ Stock Agent is now running on AWS EC2!

**Access your agent:**
- API: `http://YOUR_EC2_PUBLIC_IP:8000`
- Documentation: `http://YOUR_EC2_PUBLIC_IP:8000/docs`
- NEST A2A: `http://YOUR_EC2_PUBLIC_IP:6000`

**Next steps:**
- Test stock analysis with different queries
- Monitor logs and performance
- Set up regular backups
- Consider adding SSL/TLS for production use

---

**Need help?** Check the troubleshooting section or review the logs for error messages.
