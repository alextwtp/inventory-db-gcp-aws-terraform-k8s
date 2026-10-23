
# =========================
# Adjutable Constants
# =========================


MAIN_FILENAME = "sample_inventory.xlsx"     # Excel file name
LAST_BACKUP = "last_backup.xlsx"
SHEET_NAME = "Inventory"             # Name of work_sheet
DATE_FMT = "%Y-%m-%d %H:%M:%S"       # Time format
WINDOW_TITLE = "Inventory Updating System"
LOW_STOCK_THRESHOLD = 5              # Red warning for low stock if item <= 5 
AUTO_LOOKUP_DELAY_MS = 300           # Debounce o.3 Secs after entered ID 


# ===================================
# Define Data Structure of Excel file
# ===================================

HEADERS = [
    "Pid", "Name",
    "Current_Quantity","Transaction_Time","Buyer",
    "Previous_Quantity", "Shipper",
]

LOG_COLORS = [
    "FFF2CC",
    "D9EAD3",
    "D0E0E3",
    "FCE5CD",
    "EAD1DC",
    "CFE2F3"
]
