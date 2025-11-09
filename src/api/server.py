"""
FastAPI server for AI4OHS Hybrid Assistant
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
import uvicorn

from ..core.assistant import AI4OHSAssistant, QueryContext


# API Models
class QueryRequest(BaseModel):
    """Request model for queries"""
    query: str = Field(..., description="User's OHS-related question")
    regulation_focus: Optional[List[str]] = Field(
        None, 
        description="Specific regulations to focus on (turkish_law, osha, iso45001, world_bank, ifc_ess)"
    )
    industry_sector: Optional[str] = Field(None, description="Industry sector")
    country: Optional[str] = Field(None, description="Country of operation")


class QueryResponse(BaseModel):
    """Response model for queries"""
    answer: str
    relevant_regulations: List[str]
    recommendations: List[str]
    references: List[str]


class RegulationSummaryResponse(BaseModel):
    """Response model for regulation summary"""
    name: str
    code: str
    description: str
    key_requirements: List[str]
    applicable_sectors: List[str]


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str


# Initialize FastAPI app
app = FastAPI(
    title="AI4OHS Hybrid Assistant API",
    description="AI-powered Occupational Health and Safety Expert Assistant for Turkish Law, OSHA, ISO45001, World Bank, and IFC ESSs",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize assistant
assistant = AI4OHSAssistant()


@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint - health check"""
    return HealthResponse(status="healthy", version="1.0.0")


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(status="healthy", version="1.0.0")


@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """
    Process an OHS-related query
    
    Example queries:
    - "What are the risk assessment requirements in Turkish OHS law?"
    - "How does OSHA define workplace hazards?"
    - "What training is required under ISO 45001?"
    """
    try:
        context = QueryContext(
            query=request.query,
            regulation_focus=request.regulation_focus,
            industry_sector=request.industry_sector,
            country=request.country
        )
        
        response = assistant.process_query(context)
        
        return QueryResponse(
            answer=response.answer,
            relevant_regulations=response.relevant_regulations,
            recommendations=response.recommendations,
            references=response.references
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/regulations", response_model=List[str])
async def list_regulations():
    """List all available regulations"""
    return assistant.supported_standards


@app.get("/regulations/{regulation_type}", response_model=RegulationSummaryResponse)
async def get_regulation_summary(regulation_type: str):
    """
    Get detailed summary of a specific regulation
    
    Available regulations:
    - turkish_law: Turkish OHS Law No. 6331
    - osha: OSHA Standards
    - iso45001: ISO 45001:2018
    - world_bank: World Bank EHS Guidelines
    - ifc_ess: IFC Environmental and Social Standards
    """
    summary = assistant.get_regulation_summary(regulation_type)
    
    if not summary:
        raise HTTPException(
            status_code=404, 
            detail=f"Regulation '{regulation_type}' not found"
        )
    
    return RegulationSummaryResponse(**summary)


@app.post("/compare")
async def compare_regulations(regulation_types: List[str]):
    """Compare multiple regulations"""
    comparison = assistant.compare_regulations(regulation_types)
    
    if not comparison:
        raise HTTPException(
            status_code=404,
            detail="No valid regulations found for comparison"
        )
    
    return comparison


def start_server(host: str = "0.0.0.0", port: int = 8000):
    """Start the API server"""
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    start_server()
