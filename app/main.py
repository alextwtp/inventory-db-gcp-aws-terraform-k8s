import os
import time
from fastapi import Depends, FastAPI, Response, status, Request, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel,field_validator
from pathlib import Path
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from sqlalchemy.sql import text

from app.db import Base, SessionLocal, engine
from app.mysql_models import Inventory  
from core.exceptions import AppError
from core.inventory_mysql_service import InventoryMySQLService
from core.item import Item
from core.logger import logger
from repository.mysql_repository import MySQLRepository

app = FastAPI(title="Inventory MySQL API")


class InventoryRequest(BaseModel):
    pid: str
    name: str = ""
    qty: int
    receiver: str = ""
    shipper: str = ""


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Perform the actual API Request processing
    
    response = await call_next(request)
    
    process_time = (time.time() - start_time) * 1000  # Convert to milliseconds (ms)
    
    # Print structured HTTP request logs
    logger.info(
        f"HTTP {request.method} {request.url.path} - Status: {response.status_code} ({process_time:.2f}ms)",
        extra={
            "custom_fields": {
                "http_method": request.method,
                "url_path": request.url.path,
                "status_code": response.status_code,
                "latency_ms": round(process_time, 2),
                "client_ip": request.client.host if request.client else None,
            }
        }
    )
    
    return response


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_service(db: Session) -> InventoryMySQLService:
    repo = MySQLRepository(db)
    return InventoryMySQLService(repo)


def item_response(item: Item, message: str) -> dict:
    return {
        "status": "success",
        "message": message,
        "item": {
            "pid": item.pid,
            "name": item.name,
            "current_qty": item.current_qty,
            "buyer": item.buyer,
            "shipper": item.shipper,
        },
    }


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)
    
BASE_DIR = Path(__file__).resolve().parent.parent
@app.get("/health", status_code=status.HTTP_200_OK)
def health_check(db: Session = Depends(get_db)):
    try:
        # Simply execute a SELECT 1 to ensure DB connection is healthy
        db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return Response(
            content=f'{{"status": "unhealthy", "reason": "{str(e)}"}}',
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            media_type="application/json"
        )



@app.get("/")
async def read_index():
    html_path = BASE_DIR / "index.html"
    return FileResponse(html_path)


@app.get("/item/{pid}")
def get_item(pid: str, db: Session = Depends(get_db)) -> dict:
    service = get_service(db)

    try:
        item = service.get_item(pid)
        return item_response(item, "Item found")
    except AppError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error") from exc


@app.post("/inventory/in")
def inventory_in(req: InventoryRequest, db: Session = Depends(get_db)) -> dict:
    service = get_service(db)

    try:
        item = service.inventory_in(
            pid=req.pid,
            name=req.name,
            qty=req.qty,
            receiver=req.receiver,
            shipper=req.shipper,
        )
        return item_response(item, "Inventory-in success")
    except AppError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error") from exc


@app.post("/inventory/out")
def inventory_out(req: InventoryRequest, db: Session = Depends(get_db)) -> dict:
    service = get_service(db)

    try:
        item = service.inventory_out(
            pid=req.pid,
            name=req.name,
            qty=req.qty,
            receiver=req.receiver,
            shipper=req.shipper,
        )
        return item_response(item, "Inventory-out success")
    except AppError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error") from exc

# ========================================================================
# Query all inventory records directly from the remote Amazon RDS database 
# ========================================================================
@app.get("/inventory/list")
def list_all_inventory(db: Session = Depends(get_db)) -> dict:
    """
    Get all inventory records directly from the remote Amazon RDS database
    """
    try:
        # 1. get all records directly from the RDS database
        items = db.query(Inventory).all()
        
        # 2. transform the retrieved data into a clean list of dictionaries
        formatted_items = []
        for row in items:
            formatted_items.append({
                "id": row.id,
                "pid": row.pid,
                "item_name": row.item_name,
                "qty": row.qty,
                "receiver": row.receiver,
                "shipper": row.shipper
            })
            
        return {
            "status": "success",
            "message": "Successfully retrieved all records from RDS",
            "total_records": len(formatted_items),
            "data": formatted_items
        }
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to retrieve records from RDS: {str(exc)}")

@app.exception_handler(Exception)
def handle_all_error(request: Request, exc: Exception): 
    status_code = getattr(exc, "status_code", 500)
    
    # For any server-side error >= 500, proactively print the Error Log 
    # and automatically attach the complete Traceback.
    if status_code >= 500:
        logger.error(
            f"Unhandled exception on {request.method} {request.url.path}: {str(exc)}",
            exc_info=True
        )
    else:
        logger.warning(
            f"Client error on {request.method} {request.url.path}: {str(exc)}"
        )

    return Response(
        content=f'{{"status": "error", "message": "{str(exc)}"}}',
        status_code=status_code,
        media_type="application/json"
    )