import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DocType(str, Enum):
    boarding_pass = "boarding_pass"
    kz_id = "kz_id"
    passport = "passport"


class DocumentCreateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    doc_type: str
    file_url: str
    file_storage_key: str
    file_bucket: str
    parsed_data: dict[str, Any]
    created_at: datetime


class DocumentListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    doc_type: str
    file_url: str
    file_storage_key: str
    file_bucket: str
    parsed_data: dict[str, Any]
    created_at: datetime


class DocumentUploadForm(BaseModel):
    doc_type: DocType = Field(..., description="Тип документа")
