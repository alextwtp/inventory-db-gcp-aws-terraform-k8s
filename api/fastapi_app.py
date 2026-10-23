import time

from typing import Optional
from fastapi import FastAPI, HTTPException, Request, APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator

from config import constants as cons
from core.exceptions import AppError, NoItemError,FileInuseError
from core.item import Item
from core.logger import logger
from core.inventory_service import InventoryService
from repository.excel_repository import ExcelRepository

app = FastAPI(title="Inventory API")
api_router = APIRouter(prefix="/api")

# Initialize the repository and service
FILE_NAME = cons.MAIN_FILENAME
repo = ExcelRepository(FILE_NAME)
service = InventoryService(repo)


class InventoryRequest(BaseModel):
    pid: str
    name: Optional[str] = None
    qty: int = Field(ge=1, description="Quantity must be greater than or equal to 1")
    receiver: Optional[str] = None
    shipper: Optional[str] = None    

    @field_validator("pid")  
    @classmethod
    def validate_and_upper_pid(cls, v: str) -> str:
        # 1. Remove leading and trailing whitespace     app1234
        cleaned_v = v.strip()
          
        # 2. Check if it is an empty string
        if not cleaned_v:
            raise ValueError("PID cannot consist entirely of blank characters.")

        # 3. Check if it contains only alphanumeric characters (to prevent special characters).  
        if not cleaned_v.isalnum():
            raise ValueError("PID can only contain English letters and numbers.")
                                    
        # 4. After passing all checks, convert to uppercase and send back.
        return cleaned_v.upper()  


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

@app.exception_handler(AppError)             # Handle custom application errors
def handle_app_error(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "data": None,
            "error": exc.__class__.__name__,
            "message": str(exc),
        }
    )


@app.exception_handler(Exception)
def handle_all_error(request, exc): 
    status_code = getattr(exc, "status_code", 500)
    
    # For any server-side error >= 500, proactively print the Error Log 
    # and automatically attach the complete Exception Stack.
    if status_code >= 500:
        logger.error(
            f"Unhandled exception on {request.method} {request.url.path}: {str(exc)}",
            exc_info=True
        )
    else:
        logger.warning(
            f"Client error on {request.method} {request.url.path}: {str(exc)}"
        )

    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "data": None,   
            "error": exc.__class__.__name__,
            "message": str(exc),
        },
    )


def success_response(data, message=None): 
    return {
        "success": True,
        "data": data,
        "error": None,
        "message": message
    }   

# ------------------------
# Get item by product ID
# ------------------------
@app.get("/")                               # Health check endpoint
def read_root():
    return {"hello": "world"}

@api_router.get("/item/{pid}")
def get_item_api(pid: str):
    service.ensure_file_dir_and_path()
    _, work_list = service.get_file_and_list()
    mode = ""
    row = service.get_row(work_list, pid, mode)                                         
    item = service.get_item(work_list, row)      
    if item is None:
        raise NoItemError("Item not found")                
    item.row = row
    return item

# ------------------------
# Add stock
# ------------------------
@api_router.post("/inventory/in")
def inventory_in(req: InventoryRequest):   
    try:
        item = service.inventory_count_in_and_write(
            pid=req.pid,
            qty=req.qty,
            name=req.name, 
            receiver=req.receiver,
            shipper=req.shipper        
        )  
        return success_response(item, "Inventory-in success")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except (PermissionError, FileInuseError) as e:
        raise HTTPException(status_code=409, detail="File is currently in use or locked.")

# ------------------------
# Remove stock
# ------------------------
@api_router.post("/inventory/out")
def inventory_out(req: InventoryRequest):
    try:
        item: Item = service.inventory_count_out_and_write(
            pid=req.pid,
            qty=req.qty,
            name=req.name, 
            receiver=req.receiver,
            shipper=req.shipper         
        )                                 
        return success_response(item, "Inventory-out success")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# Register API routes after all endpoints are defined
app.include_router(api_router)