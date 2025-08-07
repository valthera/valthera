# Concepts Create

This Lambda function creates a new concept for a project.

## Development

```bash
cd lambdas/functions/concepts/create
poetry install
poetry run pytest
```

## Deployment

This function is deployed as part of the SAM template.

## Environment Variables

- `ENVIRONMENT`: Deployment environment
- `LOG_LEVEL`: Logging level
- `MAIN_TABLE_NAME`: DynamoDB main table name
- `AWS_ENDPOINT_URL`: Local DynamoDB endpoint (for development)

## API Endpoints

- **POST** `/projects/{projectId}/concepts` - Create a new concept
- **OPTIONS** `/projects/{projectId}/concepts` - CORS preflight

## Request Body

```json
{
  "name": "Concept Name",
  "description": "Concept description (optional)"
}
```

## Response Format

```json
{
  "concept_id": "uuid-string",
  "name": "Concept Name",
  "description": "Concept description",
  "project_id": "project-uuid",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

## Dependencies

- `boto3`: AWS SDK for DynamoDB access
- `valthera-core`: Shared business logic and utilities
- Standard library: `uuid`, `datetime`, `decimal`, `json` 