from core.item import Item
from core.exceptions import (
    NameLackError,
    NegativeError,
    NoItemError,
    NoneListError,
    StockShortError,
    UnknownError,
)

class InventoryService:
    
    def __init__(self, repo):
        self.repo = repo
        
    def ensure_file_dir_and_path(self):
        self.repo.ensure_filepath(self.repo.file_path()) 
        return                                         
        
    def make_qty_to_int(self, item_id):
        qty = self.repo.qty_to_int(item_id.current_qty)
        if qty < 0:           
            raise NegativeError("""The quantity cannot be negative.""")     
        return qty                      
    
    def get_file_and_list(self):
        work_file, work_list = self.repo.load_file_and_list(self.repo.file_path())                    
        if not work_file or not work_list:
            raise NoneListError("Failed to read file") 
        return work_file, work_list
    
    def get_row(self, work_list, pid, mode):            
        row = self.repo.find_row_by_id(work_list, pid)       
        return row  

    def get_item(self,work_list,row) -> Item | None:       
        if row is None: 
            return                                                          
        item: Item = self.repo.read_item(work_list, row)                   
        if not item:            
            raise NoItemError("Item not found")            
        return item
    
    def inventory_count_in_and_write(self, pid, name, qty, receiver, shipper) -> Item:
        mode = "IN"
        current_qty = 0
        row = 0
        self.ensure_file_dir_and_path()
        work_file, work_list = self.get_file_and_list()        
        row = self.get_row(work_list, pid, mode)                  
                
        if row is None:             
            row = work_list.max_row + 1              
        else:  
            item = self.get_item(work_list, row)
            current_qty = item.current_qty            
        receiver = ""
        shipper = ""                                                                                      
        new_qty = self.inventory_calculate(mode, current_qty, qty)                                 
        item = self.prepare_write (mode, row, name, pid, current_qty, qty, receiver, shipper, new_qty)
        return item 

    def inventory_count_out_and_write(self, pid, name, qty, receiver, shipper) ->Item:
        mode = "OUT"
        row =0       
        current_qty = 0
        
        self.ensure_file_dir_and_path()
        work_file, work_list= self.get_file_and_list()               
        row = self.get_row(work_list, pid, mode)  
        if not row:            
            raise NoItemError("Item not found")                 
        if not receiver or not shipper:
            raise NameLackError("Buyer and shipper names must be provided for stock-out operations.") 
        
        item = self.get_item(work_list, row)              
        current_qty = item.current_qty                                                                                         
        new_qty = self.inventory_calculate(mode, current_qty, qty) 
        item = self.prepare_write(mode, row, name, pid, current_qty, qty, receiver, shipper, new_qty)       
        return item               
    
    def prepare_write(self, mode, row, name, pid, current_qty, qty, receiver, shipper, new_qty) -> Item:                       
        item: Item = self.repo.complete_the_write(mode, row, name, pid, current_qty, qty, receiver, shipper, new_qty)
        return item    

    def inventory_calculate(self,mode: str,current_qty: int, qty: int) -> int:  
        if qty < 0:  
            raise NegativeError("The quantity cannot be negative.")
        if mode == "IN":
            new_qty = current_qty + qty            
            return new_qty
        if mode == "OUT":            
            if qty > current_qty:
                raise StockShortError("Insufficient inventory quantity.")
            else:               
                new_qty = current_qty - qty                
                return new_qty        
            
        raise UnknownError("Unknown mode")       