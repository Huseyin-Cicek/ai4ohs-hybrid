"""
OHS Regulations Knowledge Base
Contains information about Turkish Law, OSHA, ISO45001, World Bank, and IFC ESSs
"""

from typing import Dict, List
from dataclasses import dataclass


@dataclass
class Regulation:
    """Represents a regulation or standard"""
    name: str
    code: str
    description: str
    key_requirements: List[str]
    applicable_sectors: List[str]


class OHSRegulations:
    """Knowledge base for OHS regulations and standards"""
    
    def __init__(self):
        self.regulations = self._initialize_regulations()
    
    def _initialize_regulations(self) -> Dict[str, Regulation]:
        """Initialize the regulations database"""
        return {
            "turkish_law": Regulation(
                name="Turkish Occupational Health and Safety Law",
                code="Law No. 6331",
                description="Turkish OHS Law (İş Sağlığı ve Güvenliği Kanunu) regulating workplace safety in Turkey",
                key_requirements=[
                    "Risk assessment must be conducted for all workplaces",
                    "Occupational safety specialists must be employed",
                    "Workplace physicians must be appointed",
                    "Emergency response plans must be prepared",
                    "Employee training on OHS is mandatory",
                    "Regular workplace inspections are required",
                    "Personal protective equipment must be provided",
                    "Work accidents and occupational diseases must be reported"
                ],
                applicable_sectors=["All sectors in Turkey"]
            ),
            "osha": Regulation(
                name="Occupational Safety and Health Administration",
                code="OSHA Standards",
                description="US federal workplace safety and health regulations",
                key_requirements=[
                    "Provide a workplace free from serious recognized hazards",
                    "Comply with OSHA standards and regulations",
                    "Ensure employees have and use safe tools and equipment",
                    "Use color codes, posters, labels, or signs to warn of hazards",
                    "Establish or update operating procedures and communicate them",
                    "Provide medical examinations when required",
                    "Provide training in a language workers can understand",
                    "Keep accurate records of work-related injuries and illnesses",
                    "Post OSHA citations and injury/illness data",
                    "Not discriminate against workers who exercise their rights"
                ],
                applicable_sectors=["All US workplaces"]
            ),
            "iso45001": Regulation(
                name="ISO 45001 - Occupational Health and Safety Management Systems",
                code="ISO 45001:2018",
                description="International standard for occupational health and safety management systems",
                key_requirements=[
                    "Leadership and worker participation",
                    "Hazard identification and risk assessment",
                    "Legal compliance and other requirements",
                    "OHS objectives and planning to achieve them",
                    "Resources, competence, and awareness",
                    "Communication and documented information",
                    "Operational controls and emergency preparedness",
                    "Performance monitoring and measurement",
                    "Incident investigation and corrective actions",
                    "Management review and continual improvement"
                ],
                applicable_sectors=["All industries globally"]
            ),
            "world_bank": Regulation(
                name="World Bank Environmental, Health and Safety Guidelines",
                code="WB EHS Guidelines",
                description="World Bank Group's Environmental, Health and Safety Guidelines",
                key_requirements=[
                    "Occupational health and safety management system",
                    "Communication and training on workplace hazards",
                    "Physical, chemical, biological, and radiological hazard controls",
                    "Monitoring workplace conditions and worker health",
                    "Prevention and preparedness for emergencies",
                    "Appropriate personal protective equipment",
                    "Special protection for women and vulnerable groups",
                    "Accommodation for workers with disabilities",
                    "Disease prevention programs",
                    "Incident reporting and investigation procedures"
                ],
                applicable_sectors=["World Bank funded projects"]
            ),
            "ifc_ess": Regulation(
                name="IFC Environmental and Social Standards",
                code="IFC Performance Standards",
                description="International Finance Corporation Environmental and Social Performance Standards",
                key_requirements=[
                    "Assessment and management of environmental and social risks",
                    "Labor and working conditions compliance",
                    "Resource efficiency and pollution prevention",
                    "Community health, safety, and security",
                    "Land acquisition and involuntary resettlement",
                    "Biodiversity conservation",
                    "Indigenous peoples rights",
                    "Cultural heritage protection",
                    "Occupational health and safety measures",
                    "Stakeholder engagement and grievance mechanisms"
                ],
                applicable_sectors=["IFC financed projects", "Private sector investments"]
            )
        }
    
    def get_regulation(self, reg_type: str) -> Regulation:
        """Get specific regulation information"""
        return self.regulations.get(reg_type.lower())
    
    def get_all_regulations(self) -> Dict[str, Regulation]:
        """Get all regulations"""
        return self.regulations
    
    def search_requirements(self, keyword: str) -> List[tuple[str, List[str]]]:
        """Search for requirements containing a keyword"""
        results = []
        keyword_lower = keyword.lower()
        
        for reg_type, regulation in self.regulations.items():
            matching_requirements = [
                req for req in regulation.key_requirements 
                if keyword_lower in req.lower()
            ]
            if matching_requirements:
                results.append((regulation.name, matching_requirements))
        
        return results
