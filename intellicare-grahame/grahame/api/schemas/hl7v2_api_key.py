"""Pydantic schemas for HL7v2 API Key management."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator
import ipaddress


class HL7v2APIKeyBase(BaseModel):
    """Base schema for HL7v2 API Key."""
    
    system_name: str = Field(..., min_length=1, max_length=255, description="Nome do sistema/hospital")
    system_identifier: str = Field(..., min_length=1, max_length=100, description="Identificador único do sistema")
    description: Optional[str] = Field(None, description="Descrição adicional")
    rate_limit_per_minute: int = Field(60, ge=0, description="Requisições por minuto (0 = sem limite)")
    allowed_ips: Optional[str] = Field(None, description="IPs permitidos (separados por vírgula)")
    notes: Optional[str] = Field(None, description="Notas administrativas")


class HL7v2APIKeyCreate(HL7v2APIKeyBase):
    """Schema for creating a new API Key."""
    
    expires_days: Optional[int] = Field(None, ge=1, description="Dias até expiração (None = nunca expira)")
    
    @field_validator('allowed_ips')
    @classmethod
    def validate_ips(cls, v: Optional[str]) -> Optional[str]:
        """Validate IP addresses and CIDR notation."""
        if not v:
            return v
        
        ips = [ip.strip() for ip in v.split(',')]
        for ip in ips:
            if not ip:
                continue
            
            try:
                # Try to parse as IP address or network
                ipaddress.ip_network(ip, strict=False)
            except ValueError:
                raise ValueError(f"Invalid IP address or CIDR notation: {ip}")
        
        return v


class HL7v2APIKeyUpdate(BaseModel):
    """Schema for updating an API Key."""
    
    system_name: Optional[str] = Field(None, min_length=1, max_length=255)
    system_identifier: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    is_active: Optional[bool] = None
    rate_limit_per_minute: Optional[int] = Field(None, ge=0)
    allowed_ips: Optional[str] = None
    notes: Optional[str] = None
    
    @field_validator('allowed_ips')
    @classmethod
    def validate_ips(cls, v: Optional[str]) -> Optional[str]:
        """Validate IP addresses and CIDR notation."""
        if v is None:
            return v
        
        if v == "":  # Allow empty string to clear whitelist
            return None
        
        ips = [ip.strip() for ip in v.split(',')]
        for ip in ips:
            if not ip:
                continue
            
            try:
                ipaddress.ip_network(ip, strict=False)
            except ValueError:
                raise ValueError(f"Invalid IP address or CIDR notation: {ip}")
        
        return v


class HL7v2APIKeyResponse(HL7v2APIKeyBase):
    """Schema for API Key response."""
    
    id: int
    api_key: str
    is_active: bool
    expires_at: Optional[datetime]
    created_at: datetime
    created_by: Optional[str]
    last_used_at: Optional[datetime]
    usage_count: int
    
    class Config:
        from_attributes = True


class HL7v2APIKeyListResponse(BaseModel):
    """Schema for listing API Keys (without the actual key)."""
    
    id: int
    system_name: str
    system_identifier: str
    description: Optional[str]
    is_active: bool
    expires_at: Optional[datetime]
    rate_limit_per_minute: int
    allowed_ips: Optional[str]
    created_at: datetime
    last_used_at: Optional[datetime]
    usage_count: int
    
    class Config:
        from_attributes = True


class IPWhitelistAddRequest(BaseModel):
    """Schema for adding IPs to whitelist."""
    
    ips: str = Field(..., description="IPs to add (comma-separated, supports CIDR)")
    
    @field_validator('ips')
    @classmethod
    def validate_ips(cls, v: str) -> str:
        """Validate IP addresses and CIDR notation."""
        ips = [ip.strip() for ip in v.split(',')]
        for ip in ips:
            if not ip:
                continue
            
            try:
                ipaddress.ip_network(ip, strict=False)
            except ValueError:
                raise ValueError(f"Invalid IP address or CIDR notation: {ip}")
        
        return v


class IPWhitelistRemoveRequest(BaseModel):
    """Schema for removing IPs from whitelist."""
    
    ips: str = Field(..., description="IPs to remove (comma-separated)")


class IPWhitelistResponse(BaseModel):
    """Schema for IP whitelist response."""
    
    api_key_id: int
    system_identifier: str
    allowed_ips: Optional[str]
    ip_count: int
    
    class Config:
        from_attributes = True

