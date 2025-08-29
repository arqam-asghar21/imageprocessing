from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
try:
    from database import SessionLocal
    from models import Business, APIAccessLog
except ImportError:
    from .database import SessionLocal
    from .models import Business, APIAccessLog
import time
from typing import Optional

security = HTTPBearer()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_business_by_api_key(api_key: str, db: Session) -> Optional[Business]:
    """Get business by API key"""
    return db.query(Business).filter(
        Business.api_key == api_key,
        Business.is_active == True
    ).first()

async def get_business_from_api_key(
    request: Request
) -> Business:
    """Get business from API key in X-API-Key header"""
    api_key = request.headers.get("X-API-Key")
    
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="X-API-Key header is required"
        )
    
    db = SessionLocal()
    try:
        business = get_business_by_api_key(api_key, db)
        
        if not business:
            raise HTTPException(
                status_code=401,
                detail="Invalid API key"
            )
        
        return business
    finally:
        db.close()

def log_api_access(
    request: Request,
    db: Session,
    business_id: Optional[int] = None,
    status_code: int = 200,
    response_time: int = 0
):
    """Log API access for monitoring"""
    log = APIAccessLog(
        business_id=business_id,
        endpoint=str(request.url.path),
        method=request.method,
        status_code=status_code,
        response_time=response_time,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    db.add(log)
    db.commit()

async def get_current_business(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Business:
    """Get current authenticated business"""
    start_time = time.time()
    
    try:
        api_key = credentials.credentials
        business = get_business_by_api_key(api_key, db)
        
        if not business:
            log_api_access(request=None, db=db, status_code=401, response_time=int((time.time() - start_time) * 1000))
            raise HTTPException(
                status_code=401,
                detail="Invalid API key"
            )
        
        log_api_access(request=None, db=db, business_id=business.id, status_code=200, response_time=int((time.time() - start_time) * 1000))
        return business
        
    except Exception as e:
        log_api_access(request=None, db=db, status_code=401, response_time=int((time.time() - start_time) * 1000))
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication"
        )

def require_business_access(business_id: int):
    """Decorator to ensure business can only access their own resources"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # This would be implemented in the actual endpoint
            # to check if the business can access the resource
            return await func(*args, **kwargs)
        return wrapper
    return decorator
