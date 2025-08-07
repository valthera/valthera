# Valthera

A video processing and AI-powered application for concept learning and video analysis.

## Quick Start for New Developers

### Prerequisites

- **Node.js** (v18 or higher)
- **Docker** and **Docker Compose**
- **pnpm** (recommended) or npm
- **AWS CLI** (for local development)

### Getting Started

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd valthera
   ```

2. **Start everything with one command**
   ```bash
   ./valthera-local start
   ```

This single command will:
- Start all Docker services (DynamoDB, LocalStack, SQS, Cognito)
- Set up the environment automatically
- Start the React development server
- Start the SAM API server

The app will be available at `http://localhost:5173`

### Authentication

When prompted for SMS verification, use the code: **123123**

### Development Workflow

- **Frontend**: React + TypeScript + Vite
- **Backend**: AWS Lambda functions (in `lambdas/`)
- **Database**: DynamoDB
- **Storage**: S3
- **Authentication**: Cognito
- **Video Processing**: Custom worker containers

### Useful Commands

```bash
# Start everything
./valthera-local start

# Restart all services
./valthera-local restart

# Complete rebuild and start
./valthera-local rebuild

# Stop all services
./valthera-local stop

# View status
./valthera-local status

# Clean up everything
./scripts/clean.sh
```

### Project Structure

- `app/` - React frontend application
- `lambdas/` - AWS Lambda functions
- `containers/` - Docker containers for video processing
- `packages/` - Shared Python packages
- `agent/` - LangGraph agent components

### Troubleshooting

1. **Port conflicts**: Make sure ports 8000, 4566, 9324, 9239, and 5173 are available
2. **Docker issues**: Ensure Docker is running and you have sufficient resources
3. **AWS CLI**: Make sure AWS CLI is installed and configured
4. **Node modules**: If you encounter issues, try `rm -rf node_modules && pnpm install`
