# 🚀 Quick Start Guide - 3D Asset Generator

## 🏠 **LOCAL SETUP (Docker Desktop)**

### **Step 1: Prerequisites**
- ✅ Docker Desktop (you have this)
- ✅ Git

### **Step 2: Run Locally**
```bash
# Clone repository
git clone <your-repo-url>
cd capstone

# Start application (one command!)
./start.sh
```

### **Step 3: Access Application**
- **Frontend**: http://localhost:3000
- **Backend**: http://localhost:8000
- **Health**: http://localhost:8000/health

### **Step 4: Test**
1. Open http://localhost:3000
2. Enter: "Create a red sphere"
3. Click "Generate 3D Asset"
4. Download the GLB file

---

## ☁️ **AWS DEPLOYMENT**

### **Step 1: Install Prerequisites**
```bash
# Install AWS CLI
msiexec.exe /i https://awscli.amazonaws.com/AWSCLIV2.msi

# Install Terraform
choco install terraform

# Configure AWS (secure - no hardcoding)
aws configure
```

### **Step 2: Update Repository URL**
Edit `aws/terraform/user_data.sh` line 22:
```bash
# Change this line:
git clone https://github.com/yourusername/capstone-blender.git app
# To your actual repo:
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git app
```

### **Step 3: Deploy to AWS**
```bash
cd aws
./deploy.sh
# Type 'y' when prompted
```

### **Step 4: Get Your URL**
After deployment:
```
✅ Deployment completed!
🌐 Application URL: http://your-alb-dns-name.amazonaws.com
```

### **Step 5: Test in AWS**
1. Open the ALB URL in browser
2. Test health: `curl http://YOUR_ALB_DNS/health`
3. Generate a 3D asset

---

## 💰 **COST MANAGEMENT**

### **Stop AWS (Save Money)**
```bash
cd aws
./stop-aws.sh
# Saves ~$2-4/day, costs only ~$0.50/day
```

### **Start AWS Again**
```bash
cd aws
./start-aws.sh
# Wait 3-5 minutes for startup
```

### **Completely Destroy (Free)**
```bash
cd aws
./destroy.sh
# Removes everything, costs $0/day
```

---

## 🔧 **Troubleshooting**

### **Local Issues**
```bash
# Restart containers
docker-compose down
docker-compose up -d

# View logs
docker-compose logs -f
```

### **AWS Issues**
```bash
# Check instances
aws ec2 describe-instances --filters "Name=tag:Name,Values=3d-generator-instance"

# Check load balancer
aws elbv2 describe-load-balancers --names 3d-generator-alb
```

---

## 📊 **Summary**

| Environment | Command | Access | Cost |
|-------------|---------|--------|------|
| **Local** | `./start.sh` | http://localhost:3000 | Free |
| **AWS Running** | `./deploy.sh` | http://ALB_DNS | ~$2-4/day |
| **AWS Stopped** | `./stop-aws.sh` | Not accessible | ~$0.50/day |
| **AWS Destroyed** | `./destroy.sh` | Not accessible | Free |

**Recommended Workflow:**
1. Develop locally with Docker
2. Deploy to AWS for testing/demo
3. Stop AWS when not in use
4. Destroy AWS when project complete
