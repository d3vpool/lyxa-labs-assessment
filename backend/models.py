from pydantic import BaseModel, Field
from typing import Optional, List



class ApplianceCreate(BaseModel):
    name: str = Field(..., min_length=1)
    wattage: int = Field(..., gt=0)
    priority: int = Field(..., ge=1)

class ApplianceStateUpdate(BaseModel):
    action: str = Field(..., pattern = "^(on|off)$")

class ApplianceOut(BaseModel):
    id: int
    name: str
    wattage: int
    priority: int
    state: str

class SystemStatus(BaseModel):
    appliance: List[ApplianceOut]
    total_load: int
    capacity: int
    remaining: int

class EventOut(BaseModel):
    id: int
    timestamp: str
    appliance_id: Optional[int]
    appliance_name: str
    action: str
    reason: str

class ErrorDetail(BaseModel):
    detail: str