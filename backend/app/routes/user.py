
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from typing import List
from ..models.user import User, UserCreate, UserInDB, Token
from ..utils.security import create_access_token, get_current_user
from ..services.user_service import UserService
from ..config import ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter()

@router.post("/register", response_model=User)
async def register_user(user: UserCreate, app=Depends(lambda: router.app)):
    db = app.mongodb
    user_service = UserService(db)
    
    # Check if user already exists
    existing_user = await user_service.get_user(user.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Create new user
    user_in_db = await user_service.create_user(user)
    return User(
        id=str(user_in_db.id),
        username=user_in_db.username,
        created_at=user_in_db.created_at,
        updated_at=user_in_db.updated_at
    )

@router.post("/login", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), app=Depends(lambda: router.app)):
    db = app.mongodb
    user_service = UserService(db)
    
    user = await user_service.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/getAll", response_model=List[User])
async def get_all_users(
    current_user: User = Depends(get_current_user),
    app=Depends(lambda: router.app)
):
    db = app.mongodb
    user_service = UserService(db)
    
    users = await user_service.get_all_users()
    return [
        User(
            id=str(user.id),
            username=user.username,
            created_at=user.created_at,
            updated_at=user.updated_at
        ) for user in users
    ]

@router.get("/{username}", response_model=User)
async def get_user(
    username: str,
    current_user: User = Depends(get_current_user),
    app=Depends(lambda: router.app)
):
    db = app.mongodb
    user_service = UserService(db)
    
    user = await user_service.get_user(username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return User(
        id=str(user.id),
        username=user.username,
        created_at=user.created_at,
        updated_at=user.updated_at
    )