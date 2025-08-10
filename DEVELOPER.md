# Valthera Local Development

Quick guide to run and monitor your local development environment.

## 🚀 Quick Start

```bash
# Start all services
./valthera-local start

# Start React app (in new terminal)
cd app && pnpm install && pnpm run dev
```

## 📋 What's Running

| Service | Port | URL | Purpose |
|---------|------|-----|---------|
| **React App** | 5173 | http://localhost:5173 | Frontend |
| **SAM API** | 3000 | http://localhost:3000 | Backend API |
| **LocalStack** | 4566 | http://localhost:4566 | S3, AWS services |
| **DynamoDB** | 8000 | http://localhost:8000 | Database |
| **ElasticMQ** | 9324 | http://localhost:9324 | SQS queues |
| **Cognito** | 9239 | http://localhost:9239 | Auth |

## 📊 Monitor Services

```bash
# Check all services status
./valthera-local status

# View all service URLs
./valthera-local urls

# Test connectivity
./valthera-local test
```

## 📊 View S3 Objects

### Command Line (Recommended)
```bash
# Install awslocal for easier commands
pip install awscli-local

# List buckets
awslocal s3 ls

# List files in bucket
awslocal s3 ls s3://valthera-datasources

# Upload file
awslocal s3 cp myfile.txt s3://valthera-datasources/

# Download file
awslocal s3 cp s3://valthera-datasources/myfile.txt ./
```

### Alternative: Standard AWS CLI
```bash
export AWS_ACCESS_KEY_ID=local
export AWS_SECRET_ACCESS_KEY=local
export AWS_DEFAULT_REGION=us-east-1

aws s3 ls --endpoint-url http://localhost:4566
aws s3 ls s3://valthera-datasources --endpoint-url http://localhost:4566
```

## 📫 View Queues

### Web Interface
- **ElasticMQ Stats**: http://localhost:9325
- **ElasticMQ API**: http://localhost:9324

### Command Line
```bash
# Queue statistics
./valthera-local sqs stats

# Peek at messages
./valthera-local sqs peek video-processor-queue

# Send test message
./valthera-local sqs send video my-test-video

# Open web interface
./valthera-local sqs web
```

## 🐑 Monitor Lambdas

```bash
# View SAM API logs
./valthera-local apps logs sam

# Follow logs in real-time
tail -f logs/sam.log

# Filter for specific function
tail -f logs/sam.log | grep ProjectGetFunction
```

## 📝 View All Logs

```bash
# All service logs
./valthera-local logs

# Specific service logs
./valthera-local logs dynamodb
./valthera-local logs localstack
./valthera-local logs cognito

# Application logs
./valthera-local apps logs sam
./valthera-local apps logs react
```

## 🗄️ Database Operations

```bash
# List tables
awslocal dynamodb list-tables

# View table contents
awslocal dynamodb scan --table-name valthera-dev-users

# Or use standard AWS CLI
aws dynamodb list-tables --endpoint-url http://localhost:8000
```

## 🔧 Common Commands

```bash
# Start/stop services
./valthera-local start
./valthera-local stop
./valthera-local restart

# Rebuild everything
./valthera-local rebuild

# Check port conflicts
./valthera-local check-ports

# Clean resources
./valthera-local clean
```

## 🐛 Troubleshooting

### Port Conflicts
```bash
# Auto-resolve conflicts
./valthera-local start-force

# Manual check
./valthera-local check-ports
```

### Missing Dependencies
```bash
# Install React deps
./valthera-local install-deps

# Rebuild environment
./valthera-local rebuild
```

### Service Issues
```bash
# Check service health
./valthera-local test

# View service logs
./valthera-local logs
```

## 🌐 Web Interfaces Summary

- **Frontend**: http://localhost:5173
- **API**: http://localhost:3000
- **Queue Stats**: http://localhost:9325
- **Health Check**: http://localhost:4566/_localstack/health

## 🔑 Test User

- **Email**: test@valthera.com
- **Password**: TestPass123!

## 📚 Need More?

```bash
# Full help
./valthera-local help

# Service-specific help
./valthera-local sqs
./valthera-local debug
```

That's it! Start with `./valthera-local start` and use the command line tools to manage your local environment. 