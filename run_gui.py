import tkinter as tk
from repository.excel_repository import ExcelRepository
from core.inventory_service import InventoryService
from ui.gui_app import InventoryApp

def main():   
    repo = ExcelRepository("inventory.xlsx")
    service = InventoryService(repo)
    root = tk.Tk()  
    InventoryApp(root, service)
    root.mainloop()

if __name__ == "__main__":
    main()