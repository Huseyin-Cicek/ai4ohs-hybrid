# AI4OHS Hybrid - User Guide

## Overview

AI4OHS Hybrid is an intelligent assistant for Occupational Health and Safety (OHS) compliance. It provides expert guidance across multiple international standards and regulations:

- **Turkish OHS Law** (Law No. 6331)
- **OSHA Standards** (US Occupational Safety and Health Administration)
- **ISO 45001:2018** (International OHS Management System)
- **World Bank EHS Guidelines** (Environmental, Health and Safety)
- **IFC Environmental and Social Standards** (International Finance Corporation)

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Setup

1. Clone the repository:
```bash
git clone https://github.com/Huseyin-Cicek/ai4ohs-hybrid.git
cd ai4ohs-hybrid
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. (Optional) Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

## Usage

### Interactive Mode

Launch the interactive assistant:

```bash
python main.py
```

You can then ask questions like:
- "What are the risk assessment requirements in Turkish OHS law?"
- "How does OSHA define workplace hazards?"
- "What training is required under ISO 45001?"
- "What are emergency preparedness requirements?"

### Single Query Mode

Ask a single question:

```bash
python main.py --query "What are PPE requirements?"
```

Focus on specific regulations:

```bash
python main.py --query "Training requirements" --focus "turkish_law,iso45001"
```

### Regulation Information

Get detailed information about a specific regulation:

```bash
python main.py --info turkish_law
python main.py --info osha
python main.py --info iso45001
python main.py --info world_bank
python main.py --info ifc_ess
```

### API Server Mode

Start the REST API server:

```bash
python main.py --api
```

The API will be available at `http://localhost:8000`

API Documentation (Swagger UI): `http://localhost:8000/docs`

#### API Endpoints

- `GET /` - Health check
- `POST /query` - Process OHS query
- `GET /regulations` - List all regulations
- `GET /regulations/{type}` - Get regulation details
- `POST /compare` - Compare multiple regulations

#### Example API Request

```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are risk assessment requirements?",
    "regulation_focus": ["turkish_law", "iso45001"],
    "country": "Turkey"
  }'
```

## Common Use Cases

### 1. Risk Assessment Guidance

```bash
python main.py --query "What are the steps for conducting a risk assessment?"
```

### 2. Training Requirements

```bash
python main.py --query "What OHS training is required for employees?"
```

### 3. Emergency Preparedness

```bash
python main.py --query "How should I prepare an emergency response plan?"
```

### 4. PPE Selection

```bash
python main.py --query "What personal protective equipment is required for construction sites?"
```

### 5. Incident Investigation

```bash
python main.py --query "What is the proper procedure for investigating workplace accidents?"
```

### 6. Compliance Comparison

```bash
python main.py --query "Compare Turkish OHS law with ISO 45001 requirements"
```

## Supported Topics

The AI4OHS Assistant can help with:

- **Risk Assessment & Management**
  - Hazard identification
  - Risk evaluation
  - Control measures
  
- **Training & Education**
  - Employee training requirements
  - Competency assessment
  - Awareness programs

- **Emergency Preparedness**
  - Emergency response plans
  - Evacuation procedures
  - First aid requirements

- **Personal Protective Equipment**
  - PPE selection
  - Maintenance requirements
  - Training on proper use

- **Incident Management**
  - Accident reporting
  - Investigation procedures
  - Corrective actions

- **Documentation & Records**
  - Required documentation
  - Record keeping
  - Audit preparation

- **Regulatory Compliance**
  - Legal requirements
  - Standard interpretations
  - Best practices

## Tips for Best Results

1. **Be Specific**: The more specific your question, the more targeted the response
   - ✅ "What are the risk assessment requirements for construction sites in Turkey?"
   - ❌ "Tell me about safety"

2. **Specify Context**: Include your industry, country, or specific regulation
   - Use the `--focus` flag to target specific regulations
   - Mention your industry sector in the query

3. **Ask Follow-up Questions**: The assistant maintains context in interactive mode

4. **Use Keywords**: Include relevant keywords like:
   - Risk assessment, training, emergency, PPE, incident
   - Specific regulation names (Turkish law, OSHA, ISO 45001)
   - Workplace types (construction, manufacturing, office)

## Troubleshooting

### Issue: Command not found
**Solution**: Make sure you're in the correct directory and Python is installed:
```bash
cd /path/to/ai4ohs-hybrid
python --version  # Should show Python 3.8+
```

### Issue: Module import errors
**Solution**: Install dependencies:
```bash
pip install -r requirements.txt
```

### Issue: API server won't start
**Solution**: Check if port 8000 is already in use:
```bash
# On Linux/Mac
lsof -i :8000

# Use a different port
API_PORT=8080 python main.py --api
```

## Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Refer to the API documentation at `/docs` endpoint
- Check the examples in the `examples/` directory

## Disclaimer

This assistant provides guidance based on established OHS standards and regulations. Always consult with qualified OHS professionals and legal experts for specific compliance requirements. The information provided should not be considered as legal advice.
