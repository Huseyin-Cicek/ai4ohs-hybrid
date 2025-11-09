# Example OHS Queries

This document contains example queries you can use with AI4OHS Hybrid Assistant.

## Risk Assessment

### General Risk Assessment
```bash
python main.py --query "What are the key steps in conducting a workplace risk assessment?"
```

### Turkish Law Specific
```bash
python main.py --query "What are the risk assessment requirements under Turkish OHS Law?" --focus "turkish_law"
```

### ISO 45001 Approach
```bash
python main.py --query "How does ISO 45001 define risk assessment methodology?" --focus "iso45001"
```

## Training Requirements

### General Training
```bash
python main.py --query "What OHS training is required for new employees?"
```

### Sector-Specific
```bash
python main.py --query "What training is required for construction workers?"
```

### Management Training
```bash
python main.py --query "What OHS training should managers and supervisors receive?"
```

## Emergency Preparedness

### Emergency Plans
```bash
python main.py --query "How do I create an emergency response plan?"
```

### Fire Safety
```bash
python main.py --query "What are the fire safety requirements for workplaces?"
```

### Evacuation Procedures
```bash
python main.py --query "What should be included in an evacuation procedure?"
```

## Personal Protective Equipment (PPE)

### PPE Selection
```bash
python main.py --query "How do I select appropriate PPE for my workplace?"
```

### Construction PPE
```bash
python main.py --query "What PPE is required for construction sites?"
```

### Healthcare PPE
```bash
python main.py --query "What PPE requirements exist for healthcare workers?"
```

## Incident Management

### Accident Reporting
```bash
python main.py --query "What is the procedure for reporting workplace accidents?"
```

### Investigation
```bash
python main.py --query "How should I investigate a workplace incident?"
```

### Near Miss Reporting
```bash
python main.py --query "What is the importance of near miss reporting?"
```

## Compliance and Documentation

### Required Documentation
```bash
python main.py --query "What OHS documentation must be maintained?"
```

### Audit Preparation
```bash
python main.py --query "How do I prepare for an OHS audit?"
```

### Record Keeping
```bash
python main.py --query "What are the record keeping requirements for workplace injuries?"
```

## Specific Regulations

### Turkish Law
```bash
python main.py --query "What are the main requirements of Turkish OHS Law 6331?"
```

### OSHA Compliance
```bash
python main.py --query "What are the key OSHA standards for manufacturing?"
```

### ISO 45001 Certification
```bash
python main.py --query "What are the steps to achieve ISO 45001 certification?"
```

### World Bank Projects
```bash
python main.py --query "What OHS requirements apply to World Bank funded projects?"
```

### IFC Standards
```bash
python main.py --query "What are IFC Environmental and Social Standards for OHS?"
```

## Sector-Specific Queries

### Construction
```bash
python main.py --query "What are the main OHS hazards in construction?"
```

### Manufacturing
```bash
python main.py --query "What OHS controls are needed in manufacturing facilities?"
```

### Healthcare
```bash
python main.py --query "What are the OHS requirements for healthcare facilities?"
```

### Office Environments
```bash
python main.py --query "What OHS considerations apply to office workplaces?"
```

## Hazard-Specific Queries

### Chemical Hazards
```bash
python main.py --query "How should chemical hazards be managed in the workplace?"
```

### Ergonomic Hazards
```bash
python main.py --query "What are ergonomic requirements for office workers?"
```

### Noise Exposure
```bash
python main.py --query "What are the requirements for managing workplace noise exposure?"
```

### Working at Heights
```bash
python main.py --query "What safety measures are required for working at heights?"
```

## Comparative Queries

### Compare Standards
```bash
python main.py --query "Compare Turkish OHS Law with ISO 45001"
```

### Multiple Regulations
```bash
python main.py --query "What are the common requirements across OSHA, ISO 45001, and Turkish law?" --focus "osha,iso45001,turkish_law"
```

## API Examples

### Basic Query
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are risk assessment requirements?"
  }'
```

### Focused Query
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What training is required?",
    "regulation_focus": ["turkish_law"],
    "industry_sector": "construction",
    "country": "Turkey"
  }'
```

### Get Regulation Details
```bash
curl -X GET "http://localhost:8000/regulations/iso45001"
```

### Compare Regulations
```bash
curl -X POST "http://localhost:8000/compare" \
  -H "Content-Type: application/json" \
  -d '["turkish_law", "osha", "iso45001"]'
```

## Interactive Mode Examples

In interactive mode, you can have natural conversations:

```
🔍 Your OHS Question: What is risk assessment?

[Assistant provides answer]

🔍 Your OHS Question: How often should it be updated?

[Assistant provides answer with context from previous question]

🔍 Your OHS Question: What about in Turkey specifically?

[Assistant provides Turkey-specific guidance]
```

## Tips for Better Queries

1. **Be specific about your context**
   - ✅ "What PPE is required for welding operations?"
   - ❌ "Tell me about safety equipment"

2. **Mention relevant standards**
   - ✅ "What does ISO 45001 require for incident investigation?"
   - ❌ "How do I investigate incidents?"

3. **Include your industry**
   - ✅ "What are OHS requirements for construction in Turkey?"
   - ❌ "What are OHS requirements?"

4. **Ask follow-up questions in interactive mode**
   - Build on previous answers
   - Seek clarification
   - Request examples
