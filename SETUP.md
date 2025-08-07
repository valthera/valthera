# Setup Instructions for Valthera

## Prerequisites

- Node.js 18+ and npm/pnpm
- Python 3.8+
- AWS CLI configured
- Docker (for local development)

## Quick Start

### 1. Clone and Install Dependencies

```bash
git clone <your-repo-url>
cd valthera

# Install frontend dependencies
cd app
npm install

# Install Python dependencies
cd ../agent
pip install -e .
```

### 2. Environment Setup

#### For Local Development

```bash
# Copy environment templates
cp app/env.local.example app/.env.local
cp env-local.template.json env-local.json
cp samconfig.template.toml samconfig.toml

# Edit the files with your configuration
# See individual sections below for details
```

#### For Production Deployment

```bash
# Deploy infrastructure first
cd cdk
npm install
cdk deploy --profile your-aws-profile

# Copy CDK outputs
cp cdk-outputs.json ../app/

# Setup environment
cd ../app
./setup-environment.sh
```

### 3. Configuration Files

#### Frontend Environment (app/.env.local)
```bash
VITE_API_BASE_URL=http://localhost:3000
VITE_COGNITO_USER_POOL_ID=your-user-pool-id
VITE_COGNITO_USER_POOL_CLIENT_ID=your-client-id
VITE_COGNITO_IDENTITY_POOL_ID=your-identity-pool-id
VITE_REGION=us-east-1
VITE_ENVIRONMENT=local
```

#### Local AWS Configuration (env-local.json)
```json
{
  "Parameters": {
    "Environment": "dev",
    "ResourcePrefix": "valthera-dev",
    "IsLocal": "true"
  }
}
```

#### SAM Configuration (samconfig.toml)
```toml
version = 0.1

[dev]
[dev.deploy.parameters]
stack_name = "valthera-dev"
region = "us-east-1"
```

### 4. Start Development

```bash
# Start frontend
cd app
npm run dev

# Start backend (in another terminal)
cd ..
./valthera-local
```

## Security Notes

- Never commit `.env*` files, `cdk-outputs.json`, or `samconfig.toml`
- Use environment variables for sensitive data
- Template files are provided for reference only
- Update `.gitignore` if adding new sensitive files

## Troubleshooting

- If you get permission errors, ensure AWS CLI is configured
- For local development, use the provided Docker setup
- Check logs in the `logs/` directory for debugging

## Local Development Setup

### 1. Create Local Configuration Files

```bash
# Copy template files for local development
cp env-local.template.json env-local.json
cp samconfig.template.toml samconfig.toml
```

### 2. Start Local Development

```bash
# Start the full local development environment
./valthera-local
```

This will:
- Start local AWS services (DynamoDB, S3, SQS)
- Start local Cognito authentication
- Start the SAM API Gateway
- Start the React development server

### 3. Access the Application

- Frontend: http://localhost:5173
- API Gateway: http://localhost:3000
- Cognito: http://localhost:9239

### 4. Clean Up

```bash
# Clean all build artifacts and containers
./scripts/clean.sh
```
