"""
AI4OHS Hybrid Assistant Core Module
Provides intelligent assistance for occupational health and safety compliance
"""

from typing import List, Dict, Optional
import json
from dataclasses import dataclass

from ..knowledge_base.regulations import OHSRegulations


@dataclass
class QueryContext:
    """Context for user queries"""
    query: str
    regulation_focus: Optional[List[str]] = None
    industry_sector: Optional[str] = None
    country: Optional[str] = None


@dataclass
class AssistantResponse:
    """Response from the assistant"""
    answer: str
    relevant_regulations: List[str]
    recommendations: List[str]
    references: List[str]


class AI4OHSAssistant:
    """
    Hybrid AI Assistant for Occupational Health and Safety
    
    Provides expert guidance on:
    - Turkish OHS Law (Law No. 6331)
    - OSHA Standards
    - ISO 45001:2018
    - World Bank EHS Guidelines
    - IFC Environmental and Social Standards
    """
    
    def __init__(self):
        self.regulations = OHSRegulations()
        self.supported_standards = [
            "turkish_law", "osha", "iso45001", "world_bank", "ifc_ess"
        ]
    
    def process_query(self, context: QueryContext) -> AssistantResponse:
        """
        Process a user query and generate a response
        
        Args:
            context: Query context with user question and preferences
            
        Returns:
            AssistantResponse with answer, regulations, and recommendations
        """
        query_lower = context.query.lower()
        
        # Determine relevant regulations based on query
        relevant_regs = self._identify_relevant_regulations(context)
        
        # Generate response based on knowledge base
        answer = self._generate_answer(context, relevant_regs)
        
        # Provide recommendations
        recommendations = self._generate_recommendations(context, relevant_regs)
        
        # Compile references
        references = self._get_references(relevant_regs)
        
        return AssistantResponse(
            answer=answer,
            relevant_regulations=[r.name for r in relevant_regs],
            recommendations=recommendations,
            references=references
        )
    
    def _identify_relevant_regulations(self, context: QueryContext) -> List:
        """Identify which regulations are relevant to the query"""
        relevant = []
        query_lower = context.query.lower()
        
        # Check for specific regulation mentions
        if "turkish" in query_lower or "turkey" in query_lower or "türk" in query_lower:
            relevant.append(self.regulations.get_regulation("turkish_law"))
        
        if "osha" in query_lower or "us" in query_lower or "united states" in query_lower:
            relevant.append(self.regulations.get_regulation("osha"))
        
        if "iso" in query_lower or "45001" in query_lower:
            relevant.append(self.regulations.get_regulation("iso45001"))
        
        if "world bank" in query_lower or "wb" in query_lower:
            relevant.append(self.regulations.get_regulation("world_bank"))
        
        if "ifc" in query_lower or "international finance" in query_lower:
            relevant.append(self.regulations.get_regulation("ifc_ess"))
        
        # If user specified focus, use that
        if context.regulation_focus:
            for reg_type in context.regulation_focus:
                reg = self.regulations.get_regulation(reg_type)
                if reg and reg not in relevant:
                    relevant.append(reg)
        
        # If no specific regulations identified, include all
        if not relevant:
            relevant = list(self.regulations.get_all_regulations().values())
        
        return [r for r in relevant if r is not None]
    
    def _generate_answer(self, context: QueryContext, relevant_regs: List) -> str:
        """Generate an answer based on the knowledge base"""
        query_lower = context.query.lower()
        
        # Build answer components
        answer_parts = []
        
        # Add context-specific guidance
        if "risk assessment" in query_lower or "risk evaluation" in query_lower:
            answer_parts.append(
                "Risk assessment is a fundamental requirement across all major OHS standards. "
                "It involves identifying hazards, evaluating risks, and implementing controls."
            )
            
            for reg in relevant_regs:
                risk_requirements = [
                    req for req in reg.key_requirements 
                    if "risk" in req.lower() or "hazard" in req.lower()
                ]
                if risk_requirements:
                    answer_parts.append(f"\n{reg.name} requires:\n" + 
                                      "\n".join(f"- {req}" for req in risk_requirements))
        
        elif "training" in query_lower or "education" in query_lower:
            answer_parts.append(
                "Employee training is critical for workplace safety and is mandated by all major OHS regulations."
            )
            
            for reg in relevant_regs:
                training_requirements = [
                    req for req in reg.key_requirements 
                    if "training" in req.lower() or "education" in req.lower() or "awareness" in req.lower()
                ]
                if training_requirements:
                    answer_parts.append(f"\n{reg.name} requires:\n" + 
                                      "\n".join(f"- {req}" for req in training_requirements))
        
        elif "emergency" in query_lower or "preparedness" in query_lower:
            answer_parts.append(
                "Emergency preparedness and response planning are essential components of OHS management."
            )
            
            for reg in relevant_regs:
                emergency_requirements = [
                    req for req in reg.key_requirements 
                    if "emergency" in req.lower() or "preparedness" in req.lower()
                ]
                if emergency_requirements:
                    answer_parts.append(f"\n{reg.name} requires:\n" + 
                                      "\n".join(f"- {req}" for req in emergency_requirements))
        
        elif "ppe" in query_lower or "personal protective equipment" in query_lower:
            answer_parts.append(
                "Personal Protective Equipment (PPE) must be provided to workers when hazards cannot be eliminated through engineering controls."
            )
            
            for reg in relevant_regs:
                ppe_requirements = [
                    req for req in reg.key_requirements 
                    if "protective equipment" in req.lower() or "ppe" in req.lower()
                ]
                if ppe_requirements:
                    answer_parts.append(f"\n{reg.name} requires:\n" + 
                                      "\n".join(f"- {req}" for req in ppe_requirements))
        
        else:
            # General overview
            answer_parts.append(
                "Based on your query, here are the relevant requirements from applicable OHS standards:"
            )
            for reg in relevant_regs[:3]:  # Limit to top 3 for general queries
                answer_parts.append(f"\n{reg.name} ({reg.code}):")
                answer_parts.append(reg.description)
        
        return "\n".join(answer_parts) if answer_parts else "Please provide more specific details about your OHS query."
    
    def _generate_recommendations(self, context: QueryContext, relevant_regs: List) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        query_lower = context.query.lower()
        
        # Common recommendations
        recommendations.append("Conduct a comprehensive risk assessment of your workplace")
        recommendations.append("Ensure all employees receive proper OHS training")
        recommendations.append("Maintain accurate documentation and records")
        
        # Context-specific recommendations
        if context.country and context.country.lower() in ["turkey", "türkiye"]:
            recommendations.append("Ensure compliance with Turkish OHS Law No. 6331")
            recommendations.append("Appoint qualified occupational safety specialists")
            recommendations.append("Engage workplace physicians as required")
        
        if "iso" in query_lower or (context.regulation_focus and "iso45001" in context.regulation_focus):
            recommendations.append("Consider ISO 45001 certification for your OHSMS")
            recommendations.append("Implement a continual improvement process")
        
        if any(term in query_lower for term in ["accident", "incident", "injury"]):
            recommendations.append("Establish clear incident reporting procedures")
            recommendations.append("Conduct thorough incident investigations")
            recommendations.append("Implement corrective and preventive actions")
        
        return recommendations
    
    def _get_references(self, relevant_regs: List) -> List[str]:
        """Get reference information for relevant regulations"""
        references = []
        
        for reg in relevant_regs:
            references.append(f"{reg.name} ({reg.code})")
        
        return references
    
    def get_regulation_summary(self, regulation_type: str) -> Optional[Dict]:
        """Get a summary of a specific regulation"""
        reg = self.regulations.get_regulation(regulation_type)
        
        if not reg:
            return None
        
        return {
            "name": reg.name,
            "code": reg.code,
            "description": reg.description,
            "key_requirements": reg.key_requirements,
            "applicable_sectors": reg.applicable_sectors
        }
    
    def compare_regulations(self, regulation_types: List[str]) -> Dict:
        """Compare multiple regulations side by side"""
        comparison = {}
        
        for reg_type in regulation_types:
            reg = self.regulations.get_regulation(reg_type)
            if reg:
                comparison[reg_type] = {
                    "name": reg.name,
                    "key_requirements_count": len(reg.key_requirements),
                    "sectors": reg.applicable_sectors
                }
        
        return comparison
