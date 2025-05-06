# backend/app/dependencies.py
from fastapi import Depends, HTTPException, status
import os
from app.models import Project
from typing import Dict, List

# This would be replaced by a proper database in production
projects_db: Dict[str, Project] = {}

def get_projects_db():
    return projects_db

def get_gemini_api_key():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Gemini API key not configured"
        )
    return api_key

def get_github_token():
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="GitHub token not configured"
        )
    return token