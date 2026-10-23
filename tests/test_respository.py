from repository.excel_repository import ExcelRepository
import shutil

app = ExcelRepository(path="data/sample_inventory.xlsx")

def test_read_item():
    path = "data/sample_inventory.xlsx"
    # execute the load command to obtain the actual worksheet object first.
    _, work_sheet = app.load_file_and_list(path)        
    row = 13
    item = app.read_item(work_sheet, row) 
    assert item.current_qty == 33

def test_write_item(tmp_path):
    # 1. Prepare the environment
    original = "data/sample_inventory.xlsx" 
    temp_file = tmp_path/"test_write.xlsx"
    shutil.copy2(original, temp_file)
    
    # 2. initialization
    app = ExcelRepository(str(temp_file))
    work_file, work_sheet = app.load_file_and_list(app.path)
    
    # 3. Dict to be written    
    new_values = {
        "Pid": "K007",
        "Name": "Test_item", 
        "Current_Quantity": 88
    }
    
    # 4. Execute write 
    app.write_item(
        work_file,
        work_sheet,
        6,
        str(temp_file),
        new_values,
    )
        
    # 5. Verify updated row data
    updated_item = app.read_item(work_sheet, 6)
    assert updated_item.current_qty == 88 