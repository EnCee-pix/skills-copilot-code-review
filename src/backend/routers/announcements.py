"""
Announcements endpoints for the High School Management System API
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from datetime import datetime
from bson import ObjectId

from ..database import announcements_collection, teachers_collection

router = APIRouter(
    prefix="/announcements",
    tags=["announcements"]
)


@router.get("/active")
def get_active_announcements() -> List[Dict[str, Any]]:
    """Get all active announcements (visible to everyone)"""
    current_time = datetime.utcnow().isoformat()
    
    # Find announcements that are currently active
    query = {
        "expiration_date": {"$gte": current_time},
        "$or": [
            {"start_date": {"$exists": False}},
            {"start_date": None},
            {"start_date": {"$lte": current_time}}
        ]
    }
    
    announcements = list(announcements_collection.find(query).sort("created_at", -1))
    
    # Convert ObjectId to string for JSON serialization
    for announcement in announcements:
        announcement["id"] = str(announcement["_id"])
        del announcement["_id"]
    
    return announcements


@router.get("/all")
def get_all_announcements(username: str) -> List[Dict[str, Any]]:
    """Get all announcements for management (requires authentication)"""
    # Verify user is authenticated
    teacher = teachers_collection.find_one({"_id": username})
    if not teacher:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Get all announcements
    announcements = list(announcements_collection.find().sort("created_at", -1))
    
    # Convert ObjectId to string for JSON serialization
    for announcement in announcements:
        announcement["id"] = str(announcement["_id"])
        del announcement["_id"]
    
    return announcements


@router.post("/")
def create_announcement(
    title: str,
    message: str,
    expiration_date: str,
    username: str,
    start_date: Optional[str] = None
) -> Dict[str, Any]:
    """Create a new announcement (requires authentication)"""
    # Verify user is authenticated
    teacher = teachers_collection.find_one({"_id": username})
    if not teacher:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Validate expiration date
    try:
        datetime.fromisoformat(expiration_date.replace('Z', '+00:00'))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid expiration date format")
    
    # Validate start date if provided
    if start_date:
        try:
            datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start date format")
    
    # Create announcement
    announcement = {
        "title": title,
        "message": message,
        "start_date": start_date,
        "expiration_date": expiration_date,
        "created_by": username,
        "created_at": datetime.utcnow().isoformat()
    }
    
    result = announcements_collection.insert_one(announcement)
    announcement["id"] = str(result.inserted_id)
    if "_id" in announcement:
        del announcement["_id"]
    
    return announcement


@router.put("/{announcement_id}")
def update_announcement(
    announcement_id: str,
    title: str,
    message: str,
    expiration_date: str,
    username: str,
    start_date: Optional[str] = None
) -> Dict[str, Any]:
    """Update an existing announcement (requires authentication)"""
    # Verify user is authenticated
    teacher = teachers_collection.find_one({"_id": username})
    if not teacher:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Validate announcement exists
    try:
        obj_id = ObjectId(announcement_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid announcement ID")
    
    existing = announcements_collection.find_one({"_id": obj_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Announcement not found")
    
    # Validate dates
    try:
        datetime.fromisoformat(expiration_date.replace('Z', '+00:00'))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid expiration date format")
    
    if start_date:
        try:
            datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start date format")
    
    # Update announcement
    update_data = {
        "title": title,
        "message": message,
        "start_date": start_date,
        "expiration_date": expiration_date,
        "updated_by": username,
        "updated_at": datetime.utcnow().isoformat()
    }
    
    announcements_collection.update_one({"_id": obj_id}, {"$set": update_data})
    
    # Return updated announcement
    updated = announcements_collection.find_one({"_id": obj_id})
    updated["id"] = str(updated["_id"])
    del updated["_id"]
    
    return updated


@router.delete("/{announcement_id}")
def delete_announcement(announcement_id: str, username: str) -> Dict[str, str]:
    """Delete an announcement (requires authentication)"""
    # Verify user is authenticated
    teacher = teachers_collection.find_one({"_id": username})
    if not teacher:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Validate and delete announcement
    try:
        obj_id = ObjectId(announcement_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid announcement ID")
    
    result = announcements_collection.delete_one({"_id": obj_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found")
    
    return {"message": "Announcement deleted successfully"}
