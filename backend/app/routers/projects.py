# backend/app/routers/projects.py
from fastapi import APIRouter, Depends, HTTPException, status
from app.models import Project, ProjectCreate, ProjectType
from app.dependencies import get_projects_db
from typing import Dict, List
import uuid
from datetime import datetime

router = APIRouter()

@router.post("/", response_model=Project)
async def create_project(project: ProjectCreate, projects_db: Dict[str, Project] = Depends(get_projects_db)):
    """Create a new translation project"""
    project_id = str(uuid.uuid4())
    new_project = Project(
        id=project_id,
        name=project.name,
        type=project.type,
        repo_url=project.repo_url,
        created_at=datetime.now()
    )
    projects_db[project_id] = new_project
    return new_project

@router.get("/", response_model=List[Project])
async def get_projects(projects_db: Dict[str, Project] = Depends(get_projects_db)):
    """Get all translation projects"""
    return list(projects_db.values())

@router.get("/{project_id}", response_model=Project)
async def get_project(project_id: str, projects_db: Dict[str, Project] = Depends(get_projects_db)):
    """Get a specific translation project by ID"""
    if project_id not in projects_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    return projects_db[project_id]

@router.put("/{project_id}", response_model=Project)
async def update_project(
    project_id: str, 
    project_update: Project, 
    projects_db: Dict[str, Project] = Depends(get_projects_db)
):
    """Update a translation project"""
    if project_id not in projects_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Update the project with new data
    projects_db[project_id] = project_update
    return project_update

@router.delete("/{project_id}", response_model=dict)
async def delete_project(project_id: str, projects_db: Dict[str, Project] = Depends(get_projects_db)):
    """Delete a translation project"""
    if project_id not in projects_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    del projects_db[project_id]
    return {"message": "Project deleted successfully"}