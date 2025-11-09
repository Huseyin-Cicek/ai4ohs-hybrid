# AI4OHS Hybrid - API Reference

## Base URL

```
http://localhost:8000
```

## Authentication

Currently, the API does not require authentication. Future versions may implement API key authentication.

## Endpoints

### Health Check

#### GET /

Check if the API is running.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

#### GET /health

Same as root endpoint, dedicated health check.

### Query Processing

#### POST /query

Process an OHS-related query and get expert guidance.

**Request Body:**
```json
{
  "query": "What are risk assessment requirements?",
  "regulation_focus": ["turkish_law", "iso45001"],
  "industry_sector": "construction",
  "country": "Turkey"
}
```

**Parameters:**
- `query` (required): The OHS-related question
- `regulation_focus` (optional): Array of regulation codes to focus on
  - Valid values: `turkish_law`, `osha`, `iso45001`, `world_bank`, `ifc_ess`
- `industry_sector` (optional): Industry sector context
- `country` (optional): Country of operation

**Response:**
```json
{
  "answer": "Risk assessment is a fundamental requirement...",
  "relevant_regulations": [
    "Turkish Occupational Health and Safety Law",
    "ISO 45001 - Occupational Health and Safety Management Systems"
  ],
  "recommendations": [
    "Conduct a comprehensive risk assessment of your workplace",
    "Ensure all employees receive proper OHS training",
    "Maintain accurate documentation and records"
  ],
  "references": [
    "Turkish Occupational Health and Safety Law (Law No. 6331)",
    "ISO 45001 - Occupational Health and Safety Management Systems (ISO 45001:2018)"
  ]
}
```

**Example cURL:**
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the training requirements?",
    "regulation_focus": ["osha"],
    "country": "United States"
  }'
```

### Regulations

#### GET /regulations

List all available regulations.

**Response:**
```json
[
  "turkish_law",
  "osha",
  "iso45001",
  "world_bank",
  "ifc_ess"
]
```

#### GET /regulations/{regulation_type}

Get detailed information about a specific regulation.

**Path Parameters:**
- `regulation_type`: One of `turkish_law`, `osha`, `iso45001`, `world_bank`, `ifc_ess`

**Response:**
```json
{
  "name": "Turkish Occupational Health and Safety Law",
  "code": "Law No. 6331",
  "description": "Turkish OHS Law (İş Sağlığı ve Güvenliği Kanunu) regulating workplace safety in Turkey",
  "key_requirements": [
    "Risk assessment must be conducted for all workplaces",
    "Occupational safety specialists must be employed",
    "Workplace physicians must be appointed",
    "Emergency response plans must be prepared",
    "Employee training on OHS is mandatory",
    "Regular workplace inspections are required",
    "Personal protective equipment must be provided",
    "Work accidents and occupational diseases must be reported"
  ],
  "applicable_sectors": [
    "All sectors in Turkey"
  ]
}
```

**Example cURL:**
```bash
curl -X GET "http://localhost:8000/regulations/turkish_law"
```

#### POST /compare

Compare multiple regulations side by side.

**Request Body:**
```json
[
  "turkish_law",
  "osha",
  "iso45001"
]
```

**Response:**
```json
{
  "turkish_law": {
    "name": "Turkish Occupational Health and Safety Law",
    "key_requirements_count": 8,
    "sectors": ["All sectors in Turkey"]
  },
  "osha": {
    "name": "Occupational Safety and Health Administration",
    "key_requirements_count": 10,
    "sectors": ["All US workplaces"]
  },
  "iso45001": {
    "name": "ISO 45001 - Occupational Health and Safety Management Systems",
    "key_requirements_count": 10,
    "sectors": ["All industries globally"]
  }
}
```

**Example cURL:**
```bash
curl -X POST "http://localhost:8000/compare" \
  -H "Content-Type: application/json" \
  -d '["turkish_law", "osha", "iso45001"]'
```

## Error Responses

### 404 Not Found

When a requested resource doesn't exist:

```json
{
  "detail": "Regulation 'invalid_name' not found"
}
```

### 500 Internal Server Error

When an unexpected error occurs:

```json
{
  "detail": "Error message describing what went wrong"
}
```

## Rate Limiting

Currently, there is no rate limiting. This may be added in future versions.

## API Documentation

Interactive API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Python Client Example

```python
import requests

# Base URL
BASE_URL = "http://localhost:8000"

# Query the assistant
def ask_question(query, focus=None):
    response = requests.post(
        f"{BASE_URL}/query",
        json={
            "query": query,
            "regulation_focus": focus,
            "country": "Turkey"
        }
    )
    return response.json()

# Get regulation info
def get_regulation(reg_type):
    response = requests.get(f"{BASE_URL}/regulations/{reg_type}")
    return response.json()

# Example usage
if __name__ == "__main__":
    # Ask a question
    result = ask_question(
        "What are risk assessment requirements?",
        focus=["turkish_law", "iso45001"]
    )
    print(result["answer"])
    
    # Get regulation details
    turkish_law = get_regulation("turkish_law")
    print(turkish_law["description"])
```

## JavaScript/Node.js Client Example

```javascript
const axios = require('axios');

const BASE_URL = 'http://localhost:8000';

// Query the assistant
async function askQuestion(query, focus = null) {
  const response = await axios.post(`${BASE_URL}/query`, {
    query: query,
    regulation_focus: focus,
    country: 'Turkey'
  });
  return response.data;
}

// Get regulation info
async function getRegulation(regType) {
  const response = await axios.get(`${BASE_URL}/regulations/${regType}`);
  return response.data;
}

// Example usage
(async () => {
  // Ask a question
  const result = await askQuestion(
    'What are risk assessment requirements?',
    ['turkish_law', 'iso45001']
  );
  console.log(result.answer);
  
  // Get regulation details
  const turkishLaw = await getRegulation('turkish_law');
  console.log(turkishLaw.description);
})();
```

## WebSocket Support

WebSocket support is not currently implemented but may be added in future versions for real-time interactions.

## Versioning

The API version is included in all responses. Current version: `1.0.0`

Future versions will maintain backward compatibility or provide versioned endpoints (e.g., `/v2/query`).
