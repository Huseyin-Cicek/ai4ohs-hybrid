# AI4OHS Hybrid

**AI for Health and Safety (OHS) Expert Assistant**

An intelligent assistant providing expert guidance on occupational health and safety compliance across multiple international standards and regulations.

## 🌟 Features

- **Multi-Standard Support**: Covers Turkish Law, OSHA, ISO 45001, World Bank, and IFC ESSs
- **Interactive CLI**: User-friendly command-line interface for natural conversations
- **REST API**: Full-featured API for integration with other systems
- **Comprehensive Knowledge Base**: Expert-level information on OHS regulations
- **Intelligent Query Processing**: Context-aware responses with actionable recommendations
- **Regulation Comparison**: Compare requirements across different standards

## 📋 Supported Standards

| Standard | Code | Coverage |
|----------|------|----------|
| **Turkish OHS Law** | Law No. 6331 | Complete Turkish workplace safety regulations |
| **OSHA** | OSHA Standards | US federal workplace safety requirements |
| **ISO 45001** | ISO 45001:2018 | International OHS management system standard |
| **World Bank** | WB EHS Guidelines | Environmental, health, and safety guidelines |
| **IFC ESS** | IFC Performance Standards | Environmental and social standards |

## 🚀 Quick Start

### Installation

1. **Clone the repository**:
```bash
git clone https://github.com/Huseyin-Cicek/ai4ohs-hybrid.git
cd ai4ohs-hybrid
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Run the assistant**:
```bash
# Interactive mode
python main.py

# Single query
python main.py --query "What are risk assessment requirements?"

# Start API server
python main.py --api
```

## 💡 Usage Examples

### Interactive Mode
```bash
python main.py
```
Ask questions naturally:
- "What are the risk assessment requirements in Turkish OHS law?"
- "How does OSHA define workplace hazards?"
- "What training is required under ISO 45001?"

### Command Line Query
```bash
python main.py --query "What PPE is required for construction sites?"
```

### Focused Query
```bash
python main.py --query "Training requirements" --focus "turkish_law,iso45001"
```

### Regulation Information
```bash
python main.py --info turkish_law
```

### API Server
```bash
python main.py --api
# Access at http://localhost:8000
# API Docs at http://localhost:8000/docs
```

## 📚 Documentation

- **[User Guide](docs/USER_GUIDE.md)** - Complete usage instructions
- **[API Reference](docs/API_REFERENCE.md)** - Full API documentation
- **[Example Queries](examples/example_queries.md)** - Sample questions and use cases

## 🏗️ Project Structure

```
ai4ohs-hybrid/
├── src/
│   ├── core/              # Core assistant logic
│   │   └── assistant.py   # Main assistant implementation
│   ├── knowledge_base/    # OHS regulations database
│   │   └── regulations.py # Regulation definitions
│   ├── api/               # REST API
│   │   └── server.py      # FastAPI server
│   └── utils/             # Utility modules
│       └── config.py      # Configuration management
├── docs/                  # Documentation
├── examples/              # Example queries and use cases
├── config/                # Configuration files
├── main.py                # Main entry point
├── requirements.txt       # Python dependencies
└── README.md
```

## 🔧 API Usage

### Start the Server
```bash
python main.py --api
```

### Query the API
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are risk assessment requirements?",
    "regulation_focus": ["turkish_law", "iso45001"]
  }'
```

### Get Regulation Details
```bash
curl "http://localhost:8000/regulations/turkish_law"
```

## 🎯 Use Cases

### Risk Assessment
Get guidance on conducting workplace risk assessments according to various standards.

### Training Programs
Understand training requirements for employees, managers, and safety professionals.

### Emergency Preparedness
Develop emergency response plans that comply with multiple regulations.

### Compliance Audits
Prepare for OHS audits and understand documentation requirements.

### Incident Management
Learn proper procedures for investigating and reporting workplace incidents.

### International Projects
Navigate requirements for projects involving World Bank or IFC financing.

## 🔍 Key Topics Covered

- Risk Assessment & Management
- Employee Training & Competency
- Emergency Preparedness & Response
- Personal Protective Equipment (PPE)
- Incident Investigation & Reporting
- Documentation & Record Keeping
- Regulatory Compliance
- Workplace Inspections
- Occupational Health Programs
- Safety Management Systems

## 🛠️ Requirements

- Python 3.8+
- FastAPI (for API mode)
- See `requirements.txt` for complete list

## ⚙️ Configuration

Copy the example configuration:
```bash
cp config/example.env .env
```

Edit `.env` with your settings:
- API host and port
- Logging level
- Optional AI API keys (for future enhancements)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for:
- Additional regulations or standards
- New features or improvements
- Bug fixes
- Documentation enhancements

## 📄 License

This project is available for use in compliance and safety management applications.

## ⚠️ Disclaimer

This assistant provides guidance based on established OHS standards and regulations. The information provided:
- Should be used as a reference tool
- Does not constitute legal advice
- Should be verified with qualified OHS professionals
- May need to be adapted to specific jurisdictions and contexts

Always consult with qualified occupational health and safety professionals and legal experts for specific compliance requirements.

## 📞 Support

- **Issues**: Open an issue on GitHub
- **Documentation**: See `docs/` directory
- **Examples**: See `examples/` directory

## 🌐 Links

- [Turkish Ministry of Labor and Social Security](https://www.ailevecalisma.gov.tr/)
- [OSHA Official Website](https://www.osha.gov/)
- [ISO 45001 Information](https://www.iso.org/iso-45001-occupational-health-and-safety.html)
- [World Bank EHS Guidelines](https://www.ifc.org/ehsguidelines)
- [IFC Performance Standards](https://www.ifc.org/performancestandards)

---

**Built with expertise in occupational health and safety compliance**
