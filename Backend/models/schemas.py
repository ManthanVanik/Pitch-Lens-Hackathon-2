# from pydantic import BaseModel, validator
# from typing import List, Dict, Optional

# New Chat Code
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime

# class WeightageUpdate(BaseModel):
#     team_strength: int = 20
#     market_opportunity: int = 20
#     traction: int = 20
#     claim_credibility: int = 20
#     financial_health: int = 20
    
#     @validator('*')
#     def check_percentage(cls, v):
#         if not 0 <= v <= 100:
#             raise ValueError('Weightage must be between 0 and 100')
#         return v
    
#     @validator('financial_health')
#     def check_total(cls, v, values):
#         total = v + sum(values.values())
#         if total != 100:
#             raise ValueError(f'Total weightage must equal 100, got {total}')
#         return v

class FounderInfo(BaseModel):
    name: str
    education: str
    professional_background: str
    previous_ventures: str

class InterviewRequest(BaseModel):
    founder_email: str
    founder_name: Optional[str] = None

# class ChatMessage(BaseModel):
#     text: str

# New Chat Code
class WeightageUpdate(BaseModel):
    team_strength: int
    market_opportunity: int
    traction: int
    claim_credibility: int
    financial_health: int

class InitiateInterviewRequest(BaseModel):
    deal_id: str
    founder_email: EmailStr
    founder_name: Optional[str] = None

class ChatMessage(BaseModel):
    message: str
    interview_token: str

class ChatResponse(BaseModel):
    message: str
    is_complete: bool
    gathered_fields: List[str]
    missing_fields: List[str]