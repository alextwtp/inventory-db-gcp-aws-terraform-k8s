import pytest
import sys
from pydantic import ValidationError
from api.fastapi_app import InventoryRequest 


def test_validate_pid_success():
    data = InventoryRequest(pid="  abc123  ", qty=1)    
    assert data.pid == "ABC123" 

def test_validate_pid_error():    
    with pytest.raises(ValidationError):
        InventoryRequest(pid="  ", qty=1)

def test_stock_short(client):
    response = client.post(
    "api/inventory/out",
    json={
        "pid": "G111",      
        "name": "Grape",
        "qty": 500,
        "receiver": "Shen",
        "shipper": "John"
    }
)   
    assert response.status_code == 409
    data = response.json()
    assert data["success"] is False
    assert data["error"] == "StockShortError" 

@pytest.fixture
def lock_excel_file(monkeypatch):
   
    def mock_locked(*args, **kwargs):
        raise PermissionError("[WinError 5] Access Denied (Mocked FileInUse)")
   
    monkeypatch.setattr("repository.excel_repository.ExcelRepository.load_file_and_list", mock_locked)
    
    yield

def test_file_inuse_error(client, lock_excel_file):   
    response = client.post(
        "api/inventory/in",
        json={
            "pid": "A001",
            "qty": 30,
            "name": "BAG",
            "receiver": "",
            "shipper": "",
        }
    )       
    assert response.status_code == 409
    assert "File is currently in use" in response.json()["detail"]
 
def test_no_item_error(client): 

    response = client.post(
    "api/inventory/out",
    json={
        "pid": "5555",
        "qty": 30,
        "name": "SPEN",
        "receiver": "Tony",
        "shipper": "Tommy"
    }
    )   
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert data["error"] == "NoItemError"

def test_negative_error(client): 
    response = client.post(
    "api/inventory/in",
    json={
        "pid": "A001",
        "qty": -9999,
        "name": "BAG",
        "receiver": "",
        "shipper": ""
    }
    )  
    assert response.status_code == 422
    error = response.json()["detail"]
    assert error[0]["loc"] == ["body", "qty"]

def test_url_error(client): 
    test_data = {
            "pid": "A001",
            "qty": 50,
            "name":"NEWMOUSE",
            "receiver":"",
            "shipper":"",                
        }  

    # The correct URL is /inventory/in,we use an error URL for testing
    response = client.post("api/inventory/innnn", json=test_data)           
    assert response.status_code == 404     
       
def test_unprocessed_error(client): 
    test_data = {
            "pid": "W005",
            "qty": 50,
            "name": 150,
            "receiver":"",
            "shipper":"",                
        }  
        
    response = client.post("api/inventory/in", json=test_data)
    error = response.json()["detail"]          
    assert response.status_code == 422  
    assert error[0]["loc"] == ["body", "name"]    
                                                         
def test_multiple_errors(client):
    # send an emytp JSON data.
    response = client.post("api/inventory/in", json={})

    assert response.status_code == 422
    errors = response.json()["detail"]     
    
    # Make sure there are two validation errors.
    assert len(errors) == 2    

    locs = [error["loc"] for error in errors]
    assert ["body", "pid"] in locs
    assert ["body", "qty"] in locs

def test_inventory_in_success(client):
    response = client.post(
        "api/inventory/in",
        json={
            "pid": "S023",          
            "name": "Strawberry",
            "qty": 10,
            "receiver": "",
            "shipper": ""
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    
def test_inventory_out_success(client):
    response = client.post(
        "api/inventory/out",
        json={
            "pid": "C001",            
            "name": "Cherry",
            "qty": 3,
            "receiver": "Alex",
            "shipper": "Bob"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True