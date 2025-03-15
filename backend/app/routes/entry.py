from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from ..models.entry import Entry, EntryCreate, EntryUpdate, EntryFilter
from ..models.user import User
from ..utils.security import get_current_user
from ..services.entry_service import EntryService

router = APIRouter()

@router.get("/{username}/entry/getAll", response_model=List[Entry])
async def get_all_entries(
    username: str,
    sort: Optional[str] = Query(None, description="Format: field,order (e.g., date,desc or amount,asc)"),
    current_user: User = Depends(get_current_user),
    app=Depends(lambda: router.app)
):
    # Validate username against current user
    if current_user.username != username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access your own entries"
        )
    
    # Parse sort parameter if provided
    sort_by = None
    sort_order = None
    if sort:
        sort_parts = sort.split(",")
        if len(sort_parts) == 2:
            sort_by, sort_order = sort_parts
    
    db = app.mongodb
    entry_service = EntryService(db)
    entries = await entry_service.get_all_entries(username, sort_by, sort_order)
    
    return entries

@router.get("/{username}/entry/getFiltered", response_model=List[Entry])
async def get_filtered_entries(
    username: str,
    type: Optional[str] = Query(None, description="Income or Expense"),
    search: Optional[str] = Query(None, description="Search term for name or description"),
    sort_by: Optional[str] = Query(None, description="Field to sort by (amount or date)"),
    sort_order: Optional[str] = Query(None, description="Sort order (asc or desc)"),
    current_user: User = Depends(get_current_user),
    app=Depends(lambda: router.app)
):
    # Validate username against current user
    if current_user.username != username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access your own entries"
        )
    
    # Validate type if provided
    if type and type not in ["Income", "Expense"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Type must be either 'Income' or 'Expense'"
        )
    
    # Create filter object
    filters = EntryFilter(
        type=type, 
        search=search,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    db = app.mongodb
    entry_service = EntryService(db)
    entries = await entry_service.get_filtered_entries(username, filters)
    
    return entries

@router.post("/{username}/entry/addNew", response_model=Entry, status_code=status.HTTP_201_CREATED)
async def create_entry(
    username: str,
    entry: EntryCreate,
    current_user: User = Depends(get_current_user),
    app=Depends(lambda: router.app)
):
    # Validate username against current user
    if current_user.username != username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only create entries for your own account"
        )
    
    db = app.mongodb
    entry_service = EntryService(db)
    created_entry = await entry_service.create_entry(username, entry)
    
    return created_entry

@router.put("/{username}/entry/{entry_id}/edit", response_model=Entry)
async def update_entry(
    username: str,
    entry_id: str,
    entry_update: EntryUpdate,
    current_user: User = Depends(get_current_user),
    app=Depends(lambda: router.app)
):
    # Validate username against current user
    if current_user.username != username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own entries"
        )
    
    db = app.mongodb
    entry_service = EntryService(db)
    
    # Check if entry exists
    existing_entry = await entry_service.get_entry(username, entry_id)
    if not existing_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entry not found"
        )
    
    # Update entry
    updated_entry = await entry_service.update_entry(username, entry_id, entry_update)
    
    return updated_entry

@router.delete("/{username}/entry/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_entry(
    username: str,
    entry_id: str,
    current_user: User = Depends(get_current_user),
    app=Depends(lambda: router.app)
):
    # Validate username against current user
    if current_user.username != username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own entries"
        )
    
    db = app.mongodb
    entry_service = EntryService(db)
    
    # Check if entry exists
    existing_entry = await entry_service.get_entry(username, entry_id)
    if not existing_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entry not found"
        )
    
    # Delete entry
    result = await entry_service.delete_entry(username, entry_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete entry"
        )

@router.get("/{username}/entry/summary")
async def get_summary(
    username: str,
    current_user: User = Depends(get_current_user),
    app=Depends(lambda: router.app)
):
    # Validate username against current user
    if current_user.username != username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access your own summary"
        )
    
    db = app.mongodb
    entry_service = EntryService(db)
    
    summary = await entry_service.get_summary(username)
    
    return summary