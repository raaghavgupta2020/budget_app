
from datetime import datetime
from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from ..models.entry import EntryCreate, EntryUpdate, EntryInDB, EntryFilter
from uuid import uuid4

class EntryService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db["entries"]
    
    async def create_entry(self, username: str, entry: EntryCreate) -> EntryInDB:
        entry_id = str(uuid4())
        entry_in_db = EntryInDB(
            id=entry_id,
            username=username,
            name=entry.name,
            description=entry.description,
            type=entry.type,
            date=entry.date,
            amount=entry.amount,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        await self.collection.insert_one(entry_in_db.dict())
        return entry_in_db
    
    async def get_entry(self, username: str, entry_id: str) -> Optional[EntryInDB]:
        entry = await self.collection.find_one({"username": username, "id": entry_id})
        if entry:
            return EntryInDB(**entry)
        return None
        
    async def get_all_entries(self, username: str, sort_by: Optional[str] = None, sort_order: Optional[str] = None) -> List[EntryInDB]:
        query = {"username": username}
        
        # Build sort criteria
        sort_criteria = []
        if sort_by:
            sort_direction = -1 if sort_order == "desc" else 1
            sort_criteria.append((sort_by, sort_direction))
        
        # Default sort by date descending if no sort specified
        if not sort_criteria:
            sort_criteria.append(("date", -1))
        
        entries = []
        cursor = self.collection.find(query).sort(sort_criteria)
        
        async for document in cursor:
            entries.append(EntryInDB(**document))
        
        return entries
    
    async def get_filtered_entries(self, username: str, filters: EntryFilter) -> List[EntryInDB]:
        query = {"username": username}
        
        # Apply filters
        if filters.type:
            query["type"] = filters.type
        
        if filters.search:
            search_regex = {"$regex": filters.search, "$options": "i"}
            query["$or"] = [
                {"name": search_regex},
                {"description": search_regex}
            ]
        
        # Build sort criteria
        sort_criteria = []
        if filters.sort_by:
            sort_direction = -1 if filters.sort_order == "desc" else 1
            sort_criteria.append((filters.sort_by, sort_direction))
        else:
            # Default sort by date descending
            sort_criteria.append(("date", -1))
        
        entries = []
        cursor = self.collection.find(query).sort(sort_criteria)
        
        async for document in cursor:
            entries.append(EntryInDB(**document))
        
        return entries
    
    async def update_entry(self, username: str, entry_id: str, entry_update: EntryUpdate) -> Optional[EntryInDB]:
        # Get existing entry
        existing_entry = await self.get_entry(username, entry_id)
        if not existing_entry:
            return None
        
        # Prepare update data
        update_data = entry_update.dict()
        update_data["updated_at"] = datetime.utcnow()
        
        await self.collection.update_one(
            {"username": username, "id": entry_id},
            {"$set": update_data}
        )
        
        # Get updated entry
        updated_entry = await self.get_entry(username, entry_id)
        return updated_entry
    
    async def delete_entry(self, username: str, entry_id: str) -> bool:
        result = await self.collection.delete_one({"username": username, "id": entry_id})
        return result.deleted_count > 0
    
    async def get_summary(self, username: str):
        # Get total income
        income_pipeline = [
            {"$match": {"username": username, "type": "Income"}},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ]
        income_result = await self.collection.aggregate(income_pipeline).to_list(length=1)
        total_income = income_result[0]["total"] if income_result else 0
        
        # Get total expense
        expense_pipeline = [
            {"$match": {"username": username, "type": "Expense"}},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ]
        expense_result = await self.collection.aggregate(expense_pipeline).to_list(length=1)
        total_expense = expense_result[0]["total"] if expense_result else 0
        
        # Calculate balance
        balance = total_income - total_expense
        
        return {
            "total_income": total_income,
            "total_expense": total_expense,
            "balance": balance
        }