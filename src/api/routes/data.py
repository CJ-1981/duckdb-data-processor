"""
Data API routes with RBAC authorization.

@MX:NOTE: Example routes demonstrating RBAC integration
"""

from typing import Dict, Any
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from src.api.auth.decorators import require_permission
from src.api.auth.dependencies import get_current_user_with_role

router = APIRouter(prefix="/api/v1/data", tags=["Data"])


class DatasetResponse(BaseModel):
    """Dataset response model."""

    dataset_id: str
    data: Dict[str, Any]
    created_at: str


@router.get("/datasets/{dataset_id}")
@require_permission("data:read")
async def read_dataset(
    dataset_id: str,
    current_user: Dict = Depends(get_current_user_with_role),
):
    """
    Read dataset endpoint.

    Args:
        dataset_id: Dataset ID
        current_user: Current user with role

    Returns:
        Dataset data
    """
    # Mock dataset data
    dataset = {
        "dataset_id": dataset_id,
        "data": {"sample": "data"},
        "created_at": "2024-01-01",
    }

    return dataset


@router.post("/datasets")
@require_permission("data:write")
async def write_dataset(
    dataset: Dict[str, Any],
    current_user: Dict = Depends(get_current_user_with_role),
):
    """
    Write dataset endpoint.

    Args:
        dataset: Dataset data
        current_user: Current user with role

    Returns:
        Created dataset info
    """
    # Mock creation
    created_id = "dataset-123"
    created_at = "2024-01-01"

    return {"dataset_id": created_id, "created_at": created_at}
