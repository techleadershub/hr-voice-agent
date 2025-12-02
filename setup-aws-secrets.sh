#!/bin/bash
# Script to set up AWS Secrets Manager for hr-voice-agent

REGION="us-east-1"  # Change to your region
SECRET_NAME="hr-voice-agent"

echo "Setting up AWS Secrets Manager for hr-voice-agent..."

# Create secret for OpenAI API Key
echo "Creating OpenAI API Key secret..."
aws secretsmanager create-secret \
  --name "${SECRET_NAME}/openai-api-key" \
  --description "OpenAI API Key for HR Voice Agent" \
  --secret-string "your-openai-api-key-here" \
  --region $REGION

# Create secret for Qdrant URL (optional)
echo "Creating Qdrant URL secret (optional)..."
aws secretsmanager create-secret \
  --name "${SECRET_NAME}/qdrant-url" \
  --description "Qdrant URL for HR Voice Agent" \
  --secret-string "https://your-qdrant-instance.com" \
  --region $REGION

# Create secret for Qdrant API Key (optional)
echo "Creating Qdrant API Key secret (optional)..."
aws secretsmanager create-secret \
  --name "${SECRET_NAME}/qdrant-api-key" \
  --description "Qdrant API Key for HR Voice Agent" \
  --secret-string "your-qdrant-api-key-here" \
  --region $REGION

echo "Secrets created! Update the secret values with:"
echo "aws secretsmanager update-secret --secret-id ${SECRET_NAME}/openai-api-key --secret-string 'YOUR_ACTUAL_KEY' --region $REGION"





