from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from ..models.user import UserCreate, UserInDB
from ..utils.security import get_password_hash, verify_password

class UserService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db["users"]
    
    async def create_user(self, user: UserCreate) -> UserInDB:
        hashed_password = get_password_hash(user.password)
        user_in_db = UserInDB(
            username=user.username,
            hashed_password=hashed_password,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        await self.collection.insert_one(user_in_db.dict())
        return user_in_db
    
    async def get_user(self, username: str):
        user = await self.collection.find_one({"username": username})
        if user:
            return UserInDB(**user)
        return None
    
    async def get_all_users(self):
        users = []
        cursor = self.collection.find({})
        async for document in cursor:
            users.append(UserInDB(**document))
        return users
    
    async def authenticate_user(self, username: str, password: str):
        user = await self.get_user(username)
        if not user:
            return False
        if not verify_password(password, user.hashed_password):
            return False
        return user