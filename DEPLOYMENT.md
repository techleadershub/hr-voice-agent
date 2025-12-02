# AWS Deployment Guide

## Prerequisites
- AWS Account
- AWS CLI configured
- Docker installed locally
- ECR repository created (or use existing)

## Environment Variables Required

The application requires the following environment variables:

### Required:
- `OPENAI_API_KEY` - OpenAI API key for LLM, TTS, and Whisper

### Optional:
- `QDRANT_URL` - Qdrant server URL (if using external Qdrant, otherwise uses local storage)
- `QDRANT_API_KEY` - Qdrant API key (if using external Qdrant)

## Deployment Steps

### 1. Build Docker Image

```bash
docker build -t hr-voice-agent:latest .
```

### 2. Test Locally

```bash
docker run -p 8000:8000 \
  -e OPENAI_API_KEY=your_key_here \
  hr-voice-agent:latest
```

### 3. Push to AWS ECR

```bash
# Login to ECR
aws ecr get-login-password --region us-south-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-south-1.amazonaws.com

# Tag image
docker tag hr-voice-agent:latest <account-id>.dkr.ecr.us-south-1.amazonaws.com/hr-voice-agent:latest

# Push
docker push <account-id>.dkr.ecr.us-south-1.amazonaws.com/hr-voice-agent:latest
```

### 4. Deploy to ECS/Fargate

#### Option A: ECS Fargate (Recommended)

#### Step 1: Set Up AWS Secrets Manager

Store sensitive environment variables in AWS Secrets Manager:

```bash
# Create OpenAI API Key secret
aws secretsmanager create-secret \
  --name "hr-voice-agent/openai-api-key" \
  --description "OpenAI API Key" \
  --secret-string "sk-your-actual-key-here" \
  --region us-south-1

# Update secret value (if already exists)
aws secretsmanager update-secret \
  --secret-id "hr-voice-agent/openai-api-key" \
  --secret-string "sk-your-actual-key-here" \
  --region us-south-1
```

Or use the provided script:
```bash
chmod +x setup-aws-secrets.sh
./setup-aws-secrets.sh
```

#### Step 2: Create ECS Task Definition

**Method 1: Using AWS Console**
1. Go to ECS → Task Definitions → Create new
2. Configure:
   - Family: `hr-voice-agent`
   - Launch type: Fargate
   - CPU: 1024 (1 vCPU)
   - Memory: 2048 (2 GB)
   - Container:
     - Image: Your ECR image URI
     - Port: 8000
     - **Environment Variables** (non-sensitive):
       - `PYTHONPATH` = `/app`
       - `DATA_DIR` = `/app/data`
     - **Secrets** (sensitive - from Secrets Manager):
       - `OPENAI_API_KEY` → `arn:aws:secretsmanager:region:account:secret:hr-voice-agent/openai-api-key`
       - `QDRANT_URL` → (optional, if using external Qdrant)
       - `QDRANT_API_KEY` → (optional, if using external Qdrant)
   - Health Check: `/health` endpoint
   - Logging: CloudWatch Logs

**Method 2: Using JSON Task Definition**
See `aws-task-definition.json.example` for a complete example.

Register the task definition:
```bash
aws ecs register-task-definition \
  --cli-input-json file://aws-task-definition.json.example \
  --region us-south-1
```

#### Step 3: Create ECS Service

1. Create ECS Cluster (if not exists)
2. Create ECS Service:
   - Task Definition: `hr-voice-agent`
   - Launch Type: Fargate
   - Network: VPC, Subnets, Security Group
   - Load Balancer: Application Load Balancer
   - Target Group: Health check on `/health`
   - Desired Count: 1+

#### Environment Variable Injection Methods

**1. AWS Secrets Manager (Recommended for sensitive data)**
- Store secrets in Secrets Manager
- Reference in task definition using `secrets` field
- ECS automatically retrieves and injects at runtime
- No secrets in task definition JSON

**2. AWS Systems Manager Parameter Store**
- Similar to Secrets Manager but for non-sensitive config
- Use `secrets` field with Parameter Store ARN
- Example: `arn:aws:ssm:region:account:parameter/hr-voice-agent/config`

**3. Direct Environment Variables (Non-sensitive only)**
- Use `environment` field in task definition
- Visible in task definition JSON
- Only for non-sensitive values like `PYTHONPATH`, `DATA_DIR`

**4. IAM Task Role (For AWS service access)**
- Task Role: Allows container to access AWS services
- Execution Role: Allows ECS to pull images, write logs, retrieve secrets

#### Example: Environment Variables in Task Definition

```json
{
  "containerDefinitions": [{
    "environment": [
      {"name": "PYTHONPATH", "value": "/app"},
      {"name": "DATA_DIR", "value": "/app/data"}
    ],
    "secrets": [
      {
        "name": "OPENAI_API_KEY",
        "valueFrom": "arn:aws:secretsmanager:us-south-1:123456789:secret:hr-voice-agent/openai-api-key"
      }
    ]
  }]
}
```

#### Required IAM Permissions

**ECS Task Execution Role** needs:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue",
        "ssm:GetParameters"
      ],
      "Resource": [
        "arn:aws:secretsmanager:*:*:secret:hr-voice-agent/*",
        "arn:aws:ssm:*:*:parameter/hr-voice-agent/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken",
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "*"
    }
  ]
}
```

#### Option B: EC2 with Docker

1. Launch EC2 instance (t3.medium or larger recommended)
2. Install Docker
3. Run container with environment variables
4. Configure security group for port 8000

### 5. Database Considerations

**Current Setup:**
- SQLite database stored in `/app/data/interviews.db` (ephemeral)
- Qdrant vector store in `/app/qdrant_data` (ephemeral)

**For Production:**
- **SQLite**: Consider migrating to RDS PostgreSQL for persistence
- **Qdrant**: Use external Qdrant Cloud or self-hosted Qdrant instance
- **Storage**: Use EFS for persistent storage if needed

### 6. Security Recommendations

1. **Secrets Management**: Store `OPENAI_API_KEY` in AWS Secrets Manager
2. **CORS**: Update CORS settings in `backend/main.py` to restrict origins
3. **HTTPS**: Use Application Load Balancer with SSL certificate
4. **VPC**: Deploy in private subnets with NAT Gateway
5. **IAM Roles**: Use IAM roles for ECS tasks (avoid hardcoding credentials)

### 7. Monitoring

- CloudWatch Logs: Container logs automatically sent
- CloudWatch Metrics: ECS service metrics
- Health Checks: `/health` endpoint for ALB health checks

### 8. Scaling

- **Horizontal Scaling**: Increase ECS service desired count
- **Auto Scaling**: Configure based on CPU/Memory metrics
- **Load Balancing**: ALB distributes traffic across tasks

## Cost Optimization

1. **Use Spot Instances**: For non-critical workloads
2. **Right-sizing**: Monitor and adjust memory/CPU
3. **Qdrant**: Use local storage for small scale, external for production
4. **Database**: SQLite is fine for MVP, migrate to RDS for scale

## Troubleshooting

1. **Health Check Failing**: Check logs for startup errors
2. **Out of Memory**: Increase task memory (sentence-transformers needs ~1GB)
3. **Slow Startup**: First run downloads model (~80MB for all-MiniLM-L6-v2)
4. **Database Errors**: Ensure `/app/data` directory is writable

