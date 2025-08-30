#!/bin/bash
# EC2 User Data Script for 3D Asset Generator

# Update system
yum update -y

# Install Docker
yum install -y docker
systemctl start docker
systemctl enable docker
usermod -a -G docker ec2-user

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/download/v2.21.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Install Git and uv
yum install -y git
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone application repository (replace with your repo)
cd /home/ec2-user
git clone https://github.com/yourusername/capstone-blender.git app
cd app

# Set permissions
chown -R ec2-user:ec2-user /home/ec2-user/app

# Create environment file
cat > .env << EOF
BLENDER_DOCKER=true
AWS_REGION=${region}
ENVIRONMENT=production
EOF

# Build and start application
docker-compose build
docker-compose up -d

# Setup log rotation
cat > /etc/logrotate.d/docker-compose << EOF
/home/ec2-user/app/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 644 ec2-user ec2-user
}
EOF

# Create startup script
cat > /etc/systemd/system/3d-generator.service << EOF
[Unit]
Description=3D Asset Generator
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/ec2-user/app
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
User=ec2-user

[Install]
WantedBy=multi-user.target
EOF

systemctl enable 3d-generator.service

# Setup CloudWatch agent (optional)
yum install -y amazon-cloudwatch-agent

# Signal completion
/opt/aws/bin/cfn-signal -e $? --stack ${AWS::StackName} --resource AutoScalingGroup --region ${region}
