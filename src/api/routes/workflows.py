"""
Workflow Routes

FastAPI routes for workflow CRUD operations.
"""

from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.auth.dependencies import get_current_user, get_db
from src.api.auth.decorators import require_permission
from src.api.models.user import User
from src.api.schemas.workflow import (
    WorkflowCreate,
    WorkflowUpdate,
    WorkflowResponse,
    WorkflowListResponse
)
from src.api.services.workflow import WorkflowService


router = APIRouter(prefix="/api/v1/workflows", tags=["Workflows"])


@router.post("", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
@require_permission("workflows:create")
async def create_workflow(
    workflow_data: WorkflowCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new workflow.

    Requires permission: workflows:create
    """
    service = WorkflowService(db)

    # Get user ID from JWT token
    owner_id = int(current_user["sub"])

    workflow = await service.create_workflow(workflow_data, owner_id)
    return workflow


@router.get("", response_model=WorkflowListResponse)
@require_permission("workflows:read")
async def list_workflows(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: dict = Depends(get_current_user),
    is_active: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """
    List workflows with pagination.

    Requires permission: workflows:read
    """
    service = WorkflowService(db)

    # Get user ID from JWT token
    owner_id = int(current_user["sub"])

    workflows, total = await service.list_workflows(
        owner_id,
        is_active=is_active,
        page=page,
        page_size=page_size
    )

    return WorkflowListResponse(
        workflows=workflows,  # type: ignore[arg-type]
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{workflow_id}", response_model=WorkflowResponse)
@require_permission("workflows:read")
async def get_workflow(
    workflow_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: dict = Depends(get_current_user)
):
    """
    Get workflow by ID.

    Requires permission: workflows:read
    """
    service = WorkflowService(db)

    # Get user ID from JWT token
    owner_id = int(current_user["sub"])

    workflow = await service.get_workflow(workflow_id, owner_id)
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )

    return workflow


@router.put("/{workflow_id}", response_model=WorkflowResponse)
@require_permission("workflows:write")
async def update_workflow(
    workflow_id: str,
    workflow_data: WorkflowUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: dict = Depends(get_current_user)
):
    """
    Update workflow.

    Requires permission: workflows:write
    """
    service = WorkflowService(db)

    # Get user ID from JWT token
    owner_id = int(current_user["sub"])

    workflow = await service.update_workflow(workflow_id, workflow_data, owner_id)
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )

    return workflow


@router.patch("/{workflow_id}", response_model=WorkflowResponse)
@require_permission("workflows:write")
async def partial_update_workflow(
    workflow_id: str,
    workflow_data: WorkflowUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: dict = Depends(get_current_user)
):
    """
    Partial update workflow.

    Requires permission: workflows:write
    """
    service = WorkflowService(db)

    # Get user ID from JWT token
    owner_id = int(current_user["sub"])

    workflow = await service.update_workflow(workflow_id, workflow_data, owner_id)
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )

    return workflow


@router.delete("/{workflow_id}", status_code=status.HTTP_204_NO_CONTENT)
@require_permission("workflows:delete")
async def delete_workflow(
    workflow_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: dict = Depends(get_current_user)
):
    """
    Delete workflow (soft delete).

    Requires permission: workflows:delete
    """
    service = WorkflowService(db)

    # Get user ID from JWT token
    owner_id = int(current_user["sub"])

    success = await service.delete_workflow(workflow_id, owner_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )

    return None
