# backend/app/models.py
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime
import uuid


class ProjectType(str, Enum):
    MANUAL_UPLOAD = "Manual Upload"
    GITHUB_REPOSITORY = "GitHub Repository"


class FileContent(BaseModel):
    path: str
    content: str
    string_count: Optional[int] = 0


class ProjectBase(BaseModel):
    name: str
    type: ProjectType
    repo_url: Optional[str] = None


class ProjectCreate(ProjectBase):
    pass


class Project(ProjectBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.now)
    files: Dict[str, str] = {}
    translations: Dict[str, Dict[str, str]] = {}
    file_translations: Dict[str, Dict[str, Dict[str, str]]] = {}


class TranslationRequest(BaseModel):
    strings: Dict[str, str]
    target_language: str
    contexts: Optional[Dict[str, str]] = {}


class TranslationResult(BaseModel):
    translations: Dict[str, str]


class GithubScanRequest(BaseModel):
    repo_url: str
    pattern_search: bool = True
    branch: Optional[str] = None


class GithubScanResult(BaseModel):
    files: Dict[str, str]