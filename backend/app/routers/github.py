# backend/app/routers/github.py
from fastapi import APIRouter, Depends, HTTPException, status
from app.models import GithubScanRequest, GithubScanResult
from app.dependencies import get_github_token
from app.services.github_service import scan_github_repository
from typing import Dict

router = APIRouter()

@router.post("/scan", response_model=GithubScanResult)
async def scan_repository(
    scan_request: GithubScanRequest,
    github_token: str = Depends(get_github_token)
):
    """Scan a GitHub repository for translatable string files"""
    try:
        # Scan the repository using the github_service function
        files = await scan_github_repository(
            repo_url=scan_request.repo_url,
            github_token=github_token,
            pattern_search=scan_request.pattern_search,
            branch=scan_request.branch
        )
        
        return {"files": files}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error scanning repository: {str(e)}"
        )