import json
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client

from app.api.deps import get_current_user, get_supabase_with_auth, User
from app.core.constants import (
    HTTP_STATUS_BAD_REQUEST,
    HTTP_STATUS_INTERNAL_SERVER_ERROR,
    HTTP_STATUS_NOT_FOUND,
)
from app.schemas.user_query_schemas import (
    UserQueryCreate,
    UserQueryInDB,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/user-queries/",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
)
async def create_user_query(
    query_in: UserQueryCreate,
    current_user: User = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_with_auth),
):
    """
    Create a new user query using Supabase client.
    
    Stores the user's natural language query and any associated preferences.
    """
    logger.info(
        f"User {current_user.id} creating query: {query_in.model_dump(exclude_none=True)}"
    )
    
    try:
        new_query = {
            "user_id": current_user.id,
            "raw_query": query_in.raw_query,
            "config_hints_json": json.dumps(query_in.config_hints_json) if query_in.config_hints_json else None,
            "status": "active",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        
        result = supabase.table("user_queries").insert(new_query).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=HTTP_STATUS_INTERNAL_SERVER_ERROR,
                detail="Failed to create user query.",
            )
        
        logger.info(
            f"User {current_user.id} successfully created query ID {result.data[0]['id']}"
        )
        return result.data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error creating query for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=HTTP_STATUS_INTERNAL_SERVER_ERROR,
            detail="Failed to create user query.",
        ) from e


@router.get("/user-queries/", response_model=list[dict])
async def list_user_queries(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_with_auth),
):
    """
    List user queries using Supabase client.
    
    - **skip**: Number of records to skip (for pagination)
    - **limit**: Maximum number of records to return
    """
    logger.info(
        f"User {current_user.id} listing queries (skip={skip}, limit={limit})"
    )
    
    try:
        result = supabase.table("user_queries").select("*").eq("user_id", current_user.id).order("created_at", desc=True).range(skip, skip + limit - 1).execute()
        
        logger.info(f"User {current_user.id} has {len(result.data)} queries.")
        return result.data
        
    except Exception as e:
        logger.exception(f"Error listing queries for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=HTTP_STATUS_INTERNAL_SERVER_ERROR,
            detail="Failed to list user queries.",
        ) from e


@router.get("/user-queries/{query_id}", response_model=dict)
async def get_user_query(
    query_id: str,
    current_user: User = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_with_auth),
):
    """
    Get a specific user query by ID using Supabase client.
    
    Only returns queries that belong to the authenticated user.
    """
    logger.info(f"User {current_user.id} requesting query ID: {query_id}")
    
    try:
        result = supabase.table("user_queries").select("*").eq("id", query_id).eq("user_id", current_user.id).execute()
        
        if not result.data:
            logger.warning(
                f"User {current_user.id} requested non-existent query ID {query_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User query not found"
            )
        
        logger.info(f"Returning query ID {query_id} to user {current_user.id}")
        return result.data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error getting query {query_id} for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=HTTP_STATUS_INTERNAL_SERVER_ERROR,
            detail="Failed to get user query.",
        ) from e


@router.delete("/user-queries/{query_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_query(
    query_id: str,
    current_user: User = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_with_auth),
):
    """
    Delete a user query using Supabase client.
    
    Only allows deletion of queries that belong to the authenticated user.
    """
    logger.info(f"User {current_user.id} deleting query ID: {query_id}")
    
    try:
        # First check if the query exists and belongs to the user
        existing = supabase.table("user_queries").select("id").eq("id", query_id).eq("user_id", current_user.id).execute()
        
        if not existing.data:
            logger.warning(
                f"User {current_user.id} tried to delete non-existent query ID {query_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User query not found"
            )
        
        # Delete the query
        result = supabase.table("user_queries").delete().eq("id", query_id).eq("user_id", current_user.id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=HTTP_STATUS_INTERNAL_SERVER_ERROR,
                detail="Failed to delete user query"
            )
        
        logger.info(f"User {current_user.id} successfully deleted query ID {query_id}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error deleting query {query_id} for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=HTTP_STATUS_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user query.",
        ) from e