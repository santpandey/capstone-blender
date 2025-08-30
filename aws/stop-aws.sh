#!/bin/bash
# Stop AWS infrastructure to save costs

echo "💰 Stopping 3D Asset Generator AWS infrastructure..."

# Scale Auto Scaling Group to 0 instances
aws autoscaling update-auto-scaling-group \
    --auto-scaling-group-name 3d-generator-asg \
    --desired-capacity 0 \
    --min-size 0

echo "✅ Infrastructure stopped!"
echo "💰 Cost savings: ~$2-4/day"
echo "📊 Only ALB and storage costs remain (~$0.50/day)"
echo ""
echo "To restart: ./start-aws.sh"
