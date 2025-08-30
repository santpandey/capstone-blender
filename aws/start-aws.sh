#!/bin/bash
# Start AWS infrastructure

echo "🚀 Starting 3D Asset Generator AWS infrastructure..."

# Scale Auto Scaling Group to 1 instance
aws autoscaling update-auto-scaling-group \
    --auto-scaling-group-name 3d-generator-asg \
    --desired-capacity 1 \
    --min-size 1 \
    --max-size 3

echo "✅ Infrastructure starting!"
echo "⏳ Please wait 3-5 minutes for the application to be ready"
echo ""
echo "🔍 Check status with:"
echo "   aws ec2 describe-instances --filters \"Name=tag:Name,Values=3d-generator-instance\""
echo ""
echo "🌐 Once ready, access your application at:"
echo "   http://$(aws elbv2 describe-load-balancers --names 3d-generator-alb --query 'LoadBalancers[0].DNSName' --output text)"
echo ""
echo "📊 Health check:"
echo "   curl http://$(aws elbv2 describe-load-balancers --names 3d-generator-alb --query 'LoadBalancers[0].DNSName' --output text)/health"
