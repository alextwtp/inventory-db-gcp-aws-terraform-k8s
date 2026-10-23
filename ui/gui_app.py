import re
import tkinter as tk
import requests
import json
from config import constants as cons
from tkinter import messagebox, simpledialog
from tkinter import Toplevel, Label, Entry, Button
from dataclasses import dataclass
from typing import Optional
from core.exceptions import (    
    NegativeError,
    NoneListError, 
    NoItemError,    
)

def normalize_id(s: str) -> str:
    """Remove leading and trailing spaces from an ID."""
    return (s or "").strip()


@dataclass
class ItemSave:
    pid: Optional[str] = ""
    item_name: Optional[str] = ""    
    current_qty: Optional[int] = 0               
    time_now: Optional[str] = ""
    buyer: Optional[str] = ""
    shipper: Optional[str] = ""
    row_index: Optional[int] = 0                 

    workfile: Optional[str] = ""
    worksheet: Optional[str] = ""


class ui_item:
    item_id: Optional[str] = ""
    name: Optional[str] = ""    
    current_qty: Optional[int] = 0             
    time_now: Optional[str] = ""
    receiver: Optional[str] = ""
    shipper: Optional[str] = ""
    last_qty: Optional[int] = 0   
    _row_: Optional[int] = 0                 


def show_custom_error(title, message):
    # pop-up window
    err_win = tk.Toplevel()
    err_win.title(title)
    
    # Set a minimum width to prevent the window from shrinking when the message is too short.

    # The message tag `wraplength` sets the text length to automatically wrap 
    # if it exceeds 350 pixels.

    msg_label = tk.Label(err_win, text=message, wraplength=350, justify="left", padx=20, pady=20)
    msg_label.pack(expand=True)

    # Close button
    tk.Button(err_win, text="Confirm", width=10, command=err_win.destroy).pack(pady=10)

def show_result_error(message):
    print("❌", message)
    messagebox.showerror("Error", message)

def show_result_success(message):
    print("✅", message)
    messagebox.showinfo("Success", message)

class InventoryApp:     
    def __init__(self, root: tk.Tk, service):        
        WINDOW_TITLE = "Inventory Update System"  
        # ---- Windows basic settings           
        self.root = root   
        self.service = service
        self.root.title(WINDOW_TITLE)
        self.root.resizable(False, False)
        self.item_save = ItemSave() 
        self.prior_pid = 0            
    
        # ---- First launch: Ensure Excel exists + daily backup
        self.service.ensure_file_dir_and_path()
        
        # ---- UI Status (mode: Inbound/Outbound)       
        self._lookup_after_id = None  
        # Used in debounce: to avoid checking Excel every time you type a word.
        self._mode = None             
        self._last_item = None  

        # ---- Tk variable (used for display/input on the UI)
        self.var_id = tk.StringVar()
        self.var_name = tk.StringVar(value="(New product, please enter the product ID)")
        self.var_nowqty = tk.StringVar(value="")
        self.var_qty = tk.StringVar()  
        
        # Initialize an empty StringVar
        self.var_warn = tk.StringVar(value="") 
        # Initialize the label; the default setting may be black or hidden.
        self.lbl_warn = tk.Label(root, textvariable=self.var_warn, fg="black")
        self.lbl_warn.grid()           
    
        # ---- Create screen elements
        self._build_ui()   

        # ---- If the ID changes, an "automatic lookup" will be scheduled.
        self.var_id.trace_add("write", lambda *_: self._schedule_auto_lookup())

        # ---- To enable employees to easily create IDs upon opening the app.
        self.ent_id.focus_set()

    def gui_error_msg1(self):  
        show_custom_error("Error", "New product cannot be shipped")      

    def gui_error_msg2(self, current_qty):
        show_custom_error("Error", f"Inventory remaining: {current_qty}")   
  
    def msg_in_or_out_warning(self):
        show_custom_error("Reminder", "Please click either [IN] or [OUT] first")          
     
    def receiver_asking(self):
        receiver = ""        
        receiver = simpledialog.askstring("Buyer", "Please enter the buyer. (required)")
        return receiver
            
    def msg_closefile_warning(self):
        messagebox.showerror("Error", "File in use, please close Excel first.") 

    def msg_str_warning(self, e):
        messagebox.showerror("Error", str(e))     

    def msgbox_id_warning(self):         
        messagebox.showwarning("Warning:", "Please enter the product number") 
        self.ent_id.focus_set()        
    
    def need_positive_warning(self):  
        messagebox.showwarning("Warning:", "Please enter a positive integer for the quantity.")
        self.ent_qty.focus_set()           

    # -------------------------
    # UI typography and event binding 
    # -------------------------
    def _build_ui(self):
        window_width = 650
        window_height = 350
        
        # 1. Get the screen width and height
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # 2. Formula for calculating the coordinates of the center
        #    x = (screen width - window width) / 2
        #    y = (Screen height - Window height) / 2
        center_x = int((screen_width - window_width) / 2)
        center_y = int((screen_height - window_height) / 2)
        # 3. Set geometric dimensions and position: width x height + X offset + Y offset
        self.root.geometry(f"{window_width}x{window_height}+{center_x}+{center_y}")
 
        pad = 10  

        tk.Label(self.root, text="Inventory update system", font=("Microsoft JhengHei", 16, "bold"))\
            .grid(row=0, column=0, columnspan=4, padx=pad, pady=(pad, 6), sticky="w")

        # [Step-1] Enter ID   
        tk.Label(self.root, text="Product ID:", font=("Microsoft JhengHei", 12))\
            .grid(row=1, column=0, padx=pad, pady=5, sticky="e")
        
        self.ent_id = tk.Entry(self.root, textvariable=self.var_id, width=22, font=("Consolas", 12))
        self.ent_id.grid(row=1, column=1, padx=0, pady=5, sticky="w")

        # Manual query / History (for supervisor use)  
        tk.Button(self.root, text="Inquiry", width=8, command=self.lookup).grid(row=1, column=2, padx=(6, 0), pady=5)
        tk.Button(self.root, text="History", width=8, command=self.show_history).grid(row=1, column=3, padx=(6, pad), pady=5)

        # [Step-2] Displays product name and inventory (updated after lookup reads Excel).
        tk.Label(self.root, text="Product Name:", font=("Microsoft JhengHei", 12))\
            .grid(row=2, column=0, padx=pad, pady=5, sticky="e")
        tk.Label(self.root, textvariable=self.var_name, font=("Microsoft JhengHei", 12, "bold"))\
            .grid(row=2, column=1, columnspan=3, padx=0, pady=5, sticky="w")

        tk.Label(self.root, text="Current Quantity:", font=("Microsoft JhengHei", 12))\
            .grid(row=3, column=0, padx=pad, pady=5, sticky="e")
        tk.Label(self.root, textvariable=self.var_nowqty, font=("Consolas", 12))\
            .grid(row=3, column=1, columnspan=3, padx=0, pady=5, sticky="w")

        # Inventory warning text
        self.lbl_warn = tk.Label(self.root, textvariable=self.var_warn, font=("Microsoft JhengHei", 11, "bold"))
        self.lbl_warn.grid(row=4, column=1, columnspan=3, padx=0, pady=(0, 6), sticky="w")
        
        # [Step-3] Choose the Action, textvariable=self.var_warn, font=("Microsoft JhengHei", 11, "bold"))
        #          It will determines the positive or negative value of delta.
        tk.Label(self.root, text="Action:", font=("Microsoft JhengHei", 12))\
            .grid(row=5, column=0, padx=pad, pady=5, sticky="e")
        self.btn_in = tk.Button(self.root, text="IN", width=12, command=lambda: self.set_mode("IN"))
        self.btn_in.grid(row=5, column=1, padx=(0, 0), pady=5, sticky="w")

        self.btn_out = tk.Button(self.root, text="OUT", width=12, command=lambda: self.set_mode("OUT"))
        self.btn_out.grid(row=5, column=2, padx=(0, 3), pady=5, sticky="w")

        # [Step-4] Input quantity (pure numbers)
        tk.Label(self.root, text="Quantity:", font=("Microsoft JhengHei", 12))\
            .grid(row=6, column=0, padx=pad, pady=5, sticky="e")

        # validate="key": Checks the key after each character is typed; if it doesn't match,
        # the input is blocked (to prevent mistaken identification).
        vcmd = (self.root.register(self._validate_qty_entry), "%P")
        self.ent_qty = tk.Entry(
            self.root, textvariable=self.var_qty, width=22, font=("Consolas", 12),
            validate="key", validatecommand=vcmd   
        )
        self.ent_qty.grid(row=6, column=1, padx=0, pady=5, sticky="w")

        tk.Label(self.root, text="Enter only numbers, for example: 3", fg="gray")\
            .grid(row=6, column=2, columnspan=2, padx=(6, pad), pady=5, sticky="w")

        # [Step-5] Confirm Update → Write Back to Form  
                           
        self.btn_confirm = tk.Button(self.root, text="Confirm Update", width=16, height=2, command=self.confirm_update)
        self.btn_confirm.grid(row=7, column=0, columnspan=4, padx=pad, pady=(10, pad)) 

        # Shortcut key:
        # - Press Enter in the ID input box: Manual Query + Jump to the Quantity field.
        # - Press Enter in the quantity box: Update directly (fastest process for employees).
        # - Esc: Quick close
        self.ent_id.bind("<Return>", lambda e: (self.lookup(), self.ent_qty.focus_set()))
        self.ent_qty.bind("<Return>", lambda e: self.confirm_update())
        self.root.bind("<Escape>", lambda e: self.root.destroy())

        # Initially: No "IN" or "OUT" option was selected, so the buttons were not highlighted.
        self._refresh_mode_buttons()
 
    def _validate_qty_entry(self, proposed: str) -> bool:
        """
        Entry instant error prevention:
        - Allows empty strings (for easy deletion and retyping)
        - Or pure numbers
        """
        if proposed == "":
            return True        
        return bool(re.fullmatch(r"\d+", proposed))

    def _schedule_auto_lookup(self):
        """
        Automatic lookup (debounce concept):
        - User typing continuously triggers traces
        - We cancel the previous AFTER statement and then reschedule
        - Only when the process stops for more than 300ms will the Excel query 
          actually be performed.
        """
        AUTO_LOOKUP_DELAY_MS = cons.AUTO_LOOKUP_DELAY_MS  
        if self._lookup_after_id is not None:
            self.root.after_cancel(self._lookup_after_id)
        self._lookup_after_id = self.root.after(AUTO_LOOKUP_DELAY_MS, self.lookup_silent)

    def _set_display_unknown(self, msg: str):
        # When an ID cannot be found or has not been entered, the screen will display.
        self.var_name.set(msg)
        self.var_nowqty.set("")
        self.var_warn.set("")
        self._last_item = None  

    def _set_display_item(self, pid: str, item: dict):
        """
        After finding the product, the screen updates as follows:
        - Displays product name and inventory
        - Detects low inventory and displays a red warning.               
        """
        LOW_STOCK_THRESHOLD = cons.LOW_STOCK_THRESHOLD         
        if item is None:
            return
        else:          
            name = str(item.name or "")            
            try:
                qty = self.service.make_qty_to_int(item)           
            except NegativeError as e:
                print(f"Input error: {e}") # Print: Input error: Quantity cannot be less than 0               
                
        self.var_name.set(name if name else "(Unnamed)")       
        self.var_nowqty.set(str(qty))    

        if qty <= LOW_STOCK_THRESHOLD:                         
            self.var_warn.set(f"⚠ Low Inventory Alert: Currently {qty} (threshold {LOW_STOCK_THRESHOLD})")
            self.lbl_warn.configure(fg="red")
        else:
            self.var_warn.set("")
            self.lbl_warn.configure(fg="black")                                                  
        # Keep information such as row (for future expansion).
        self._last_item = item
        self._last_pid = item.pid   

    def _refresh_mode_buttons(self):
        """
        A mini UX: Letting employees know whether they selected "IN" or "Out"
        The `relief="sunken"` attribute in tkinter looks like it's been pressed down.
        """
        if self._mode == "IN":
            self.btn_in.configure(relief="sunken")
            self.btn_out.configure(relief="raised")
        elif self._mode == "OUT":
            self.btn_in.configure(relief="raised")
            self.btn_out.configure(relief="sunken")
        else:
            self.btn_in.configure(relief="raised")
            self.btn_out.configure(relief="raised")

    def set_mode(self, mode: str):
        """Set the mode after receiving ("IN")/shipping("OUT") goods, and move the focus 
           to the quantity field (to speed up the operation).
        """        
        self._mode = mode
        self._refresh_mode_buttons()
        self.ent_qty.focus_set()
    
    # ==============================================================================
    # [Core Process-1] Query: Enter ID → Read Excel → Display Product Name/Inventory
    # ==============================================================================
    def lookup_silent(self):
        """
        Automatic query version (silent):   
        - No pop-up message boxes
        - Only updates the screen (more like a "real-time notification")
        """
        pid = normalize_id(self.var_id.get())             
        try:
            self.validate_the_pid(pid)                        
        except ValueError:
            self._set_display_unknown("(Please enter the correct ID)")
            return

        try:                                        
            work_file, work_list = self.service.get_file_and_list()                                  
        except NoneListError: 
            self._set_display_unknown("Failed to read file")                      
            return
        
        self.item_save.workfile = work_file
        self.item_save.worksheet = work_list

        mode = self._mode
        row = 0
        
        try:
            row = self.service.get_row(work_list, pid, mode)                                                       
        except NoItemError:                                   
            self._set_display_unknown("(This ID cannot be found, please re-enter)")
            return
        
        if pid == self.prior_pid:            
            self.save_prior_information(pid, row, work_list)
            return

        if row is not None:
            try:               
                item = self.service.get_item(work_list, row)                                                                                                                     
                item.row = row                    
                self.save_item_information(item, row)                
                self._set_display_item(pid, item) 
            except NoItemError:                                               
                self._set_display_unknown("(This ID cannot be found, please re-enter)")
                return
   
    def validate_the_pid(self, pid) -> str:  
        
        # 2. Check if it is an empty string
        if not pid:
            raise ValueError("PID cannot be all blank characters.")         
                
        # 3. Check if it contains only alphanumeric characters (to prevent special characters). 
        if not pid.isalnum():  
            raise ValueError("PID can only contain alphanumeric characters.")
            
        # 4. Passed all checks, converted to uppercase, and then return.
        self.var_id.set(pid.upper())  
        return pid

    def save_prior_information(self, pid, row, work_list):
        item = self.service.get_item(work_list, row)
        self.item_save.pid = ui_item.pid                     
        self.item_save.item_name = ui_item.name
        self.item_save.current_qty = ui_item.current_qty
        self.item_save.time_now = ui_item.time_now       
        self.item_save.buyer = ui_item.receiver
        self.item_save.shipper = ui_item.shipper     
        self.item_save.row_index = ui_item._row_ 
        self.var_name.set(str(ui_item.name))
        self.var_nowqty.set(str(ui_item.current_qty))        
    
    def lookup(self):
        """
        Manual search version (press button or ID and press Enter):
        - If not found, a pop-up window will prompt the user on how to 
          add the account.
        """
        pid = normalize_id(self.var_id.get())

        if not pid:
            messagebox.showwarning("Warning", "Please enter the product ID.")
            self.ent_id.focus_set()
            return
        
        try:
            work_file, work_list = self.service.get_file_and_list()           
        except NoneListError as e:
            messagebox.showerror("Failed to read file", str(e))
            return  

        mode = self._mode    
        try:
            row = self.service.get_row(work_list, pid, mode)
        except NoItemError:                       
            self._set_display_unknown("(This number cannot be found, please re-enter)")
            messagebox.showinfo(
                "Search Results",
                f"ID not found: {pid}\n\nTo add a new product:\n1) Press [IN]\n2) Enter the quantity\n3) Press [Confirm Update]"
                )
            return      
       
        try:          
            item = self.service.get_item(work_list, row)       
        except NoItemError:           
            self._set_display_unknown("(This Item cannot be found)")
            return                                       
                  
        if row is not None:           
            item.row = row                         
        self._set_display_item(pid, item)
    
    def is_positive_int_str(self, s: str) -> bool:
        """
        Quantity Input Rules :
        - Must be purely numeric
        - And > 0
        """
        s = (s or "").strip()
        if not re.fullmatch(r"\d+", s):
            return False
        return int(s) > 0
    
    # ============================================================================
    # [Core Process - 2] History: Displays the current/previous/two previous times.
    # =============================================================================
    def show_history(self): 
        "Press the 'History' button: A small window will open displaying three versions."
        pid = normalize_id(self.var_id.get())
        if not pid:
            messagebox.showwarning("Warning", "Please enter the product ID first.")
            return

        try:
            workfile, work_list = self.service.get_file_and_list()  ####
        except NoneListError:
            messagebox.showerror("Failed to read file")
            return
        
        mode = self._mode
        try:
            row = self.service.get_row(work_list, pid, mode)
        except NoItemError:
            messagebox.showinfo("History", f"ID not found:{pid}")
            return

        try:   
            item = self.service.get_item(work_list, row)                                             
        except NoItemError:
            self._set_display_unknown("(Item not found)")
            return                                                      
        
        name = (str(item.name) or "")
        
        def fmt(q, d):
            # Make None / empty values ​​display as (empty), otherwise it looks like a bug.                    
            qv = getattr(item, q, None)  
            dv = getattr(item, d, None)            
            qv = "(Empty)" if qv is None or str(qv).strip() == "" else str(qv)
            dv = "(Empty)" if dv is None or str(dv).strip() == "" else str(dv)
            return qv, dv
        
        now_q, now_d = fmt("current_qty", "time_now")        
        p1_q, p1_d = fmt("previous_qty", "")  
                          
        top = tk.Toplevel(self.root)
        top.title("Historical records")
        top.resizable(False, False)  

        pad = 12
        tk.Label(top, text=f"ID: {pid}", font=("Microsoft JhengHei", 12, "bold"))\
            .grid(row=0, column=0, columnspan=3, padx=pad, pady=(pad, 4), sticky="w")
        tk.Label(top, text=f"Name: {name}", font=("Microsoft JhengHei", 12))\
            .grid(row=1, column=0, columnspan=3, padx=pad, pady=(0, 10), sticky="w")

        for c, h in enumerate(["Version", "Quantity", "Date"]):
            tk.Label(top, text=h, font=("Microsoft JhengHei", 11, "bold"))\
                .grid(row=2, column=c, padx=pad, pady=(0, 6), sticky="w")

        rows = [("Current", now_q, now_d), ("Previous", p1_q, p1_d)]
        for i, (ver, q, d) in enumerate(rows, start=3):
            tk.Label(top, text=ver, font=("Microsoft JhengHei", 11))\
                .grid(row=i, column=0, padx=pad, pady=3, sticky="w")
            tk.Label(top, text=q, font=("Consolas", 11))\
                .grid(row=i, column=1, padx=pad, pady=3, sticky="w")
            tk.Label(top, text=d, font=("Consolas", 11))\
                .grid(row=i, column=2, padx=pad, pady=3, sticky="w")

        tk.Button(top, text="Close", command=top.destroy, width=10)\
            .grid(row=10, column=0, columnspan=3, padx=pad, pady=(10, pad))

    # =============================================================================
    # [Core Process - 3] Update: Purchase/Shipment + Quantity → Write Back to Excel
    # =============================================================================
    def confirm_update(self):     
    
        pid = normalize_id(self.var_id.get())            
        if not pid:                                        
            self.msgbox_id_warning() 
            return 

        if self._mode not in ("IN", "OUT"):     
            self.msg_in_or_out_warning()              
            return          
                        
        qty_str = (self.var_qty.get() or "").strip()
        qty = int(qty_str)              
        mode = self._mode 
        new_qty = 0  
        row = 0        
        receiver = ""       
        delta = qty if mode == "IN" else -qty  # Purchases: +Value Sales: -Value        
                    
        if not self.is_positive_int_str(qty_str) or qty == 0:   
            self.need_positive_warning()         
            return         
        if self.item_save.row_index > 0:
            row = self.item_save.row_index                           
        if row == 0:
            if delta < 0:                
                messagebox.showerror("Error", "New products cannot be shipped.")
                return
            item_name = simpledialog.askstring("New product", f"cannot find ID:{pid}.Please enter the product name:")
            if not item_name:
                return                                                                                              
        
        # ===== Required fields for buyer and shipper in shipments =====
        receiver = ""                 
        shipper = ""
        if self._mode == "OUT":       
            receiver = self.receiver_asking_color()
            if not receiver:
                return
            shipper = self.shipper_asking_color()
            if not shipper:
                return                                                    
        if row == 0:
            row = self.item_save.worksheet.max_row + 1                                  
        else: 
            pid = self.item_save.pid            
            item_name = self.item_save.item_name
            current_qty = self.item_save.current_qty           
            row = self.item_save.row_index                        
        payload = {
            "pid": pid,
            "name": item_name,
            "qty": qty,                
            "receiver": receiver,
            "shipper": shipper,                
        }        
                           
        if mode == "IN": 
            print("🔥 call IN API")
            response = requests.post(
                "http://127.0.0.1:8000/api/inventory/in",
                json=payload,
            )
        else:
            print("🔥 call OUT API")
            response = requests.post(
                "http://127.0.0.1:8000/api/inventory/out",
                json=payload,
            )
        
        result = response.json()        
        data = json.loads(response.text)
        inner_data = data.get('data')                                 
          
        if not result["success"]:            
            # 1️⃣ Error displayed
            show_result_error(result["message"])            
            # 2️⃣ Stop the process (extremely important)
            return       
       
        show_result_success(result["message"])
        data = json.loads(response.text)
        inner_data = data.get('data')                                   
         
        # ========= UI data (separate from Excel) =========
        ui_item.pid = inner_data["pid"]
        ui_item.name = inner_data["name"] 
        ui_item.current_qty = inner_data["current_qty"]                     
        ui_item.time_now = inner_data["time_now"]
        ui_item.receiver = inner_data["buyer"]
        ui_item.last_qty = inner_data["previous_qty"]
        ui_item.shipper = inner_data["shipper"]
        ui_item._row_ = inner_data["row"]  
                                                  
        self._set_display_item(pid, ui_item)
        self.prior_pid = pid
        self._reset_for_next() 
       
        action = "IN" if delta > 0 else "OUT"
        extra = f"\nBuyer:{receiver}" if self._mode == "OUT" and receiver else ""         
        
        messagebox.showinfo(
            "Finished",
            f"Update successful\n\nID:{ui_item.pid}\nName:{ui_item.name}\n"
            f"Mode:{action}\nQuantity:{abs(delta)}\nCurrent Quantity:{ui_item.current_qty}"
            f"{extra}"
        )    
    
    def _reset_for_next(self): 
        """ 
        Updated UX:
        - Clear quantity
        - Cancel mode (to avoid errors caused by forgetting to switch modes for 
          the next entry)
        - Focus back to IDs and select all (for easy entry of the next ID)
        """
        self.var_qty.set("") 
        self.var_id.set("")
        self.item_save.row_index = 0
        self._mode = None            
        self._refresh_mode_buttons()
        self.ent_id.focus_set()
        self.ent_id.selection_range(0, tk.END)   
           
    def save_item_information(self, item, row):                                                    
        self.item_save.pid = item.pid                     
        self.item_save.item_name = item.name
        self.item_save.current_qty = item.current_qty
        self.item_save.time_now = item.time_now       
        self.item_save.buyer = item.buyer  
        self.item_save.shipper = item.shipper     
        self.item_save.row_index = row     

    def receiver_asking_color(self):
        self.root.withdraw()
        receiver = ""
        asking_count = 0
        while not receiver:            
            # Color Green - for Buyer
            receiver = self.custom_askstring(
                "Receiving Procedure",
                "Please enter the buyer's name (required):",
                "#E8F5E9",
            )
            asking_count = asking_count + 1
            if asking_count >= 3:
                show_custom_error("Error", "Without a Buyer, this transaction will not be valid.")
                break
        self.root.deiconify()
        return receiver.strip()

    def shipper_asking_color(self):
        self.root.withdraw()
        shipper = ""
        asking_count = 0
        while not shipper:    
            # Color Yellow - for Shipper
            shipper = self.custom_askstring(
                "Shipping Procedure",
                "Please enter the shipper's name (required):",
                "#FFF9C4",
            )           
            asking_count = asking_count + 1
            if asking_count >= 3:
                show_custom_error("Error", "Without a shipper, this transaction will not be valid.")
                break
        self.root.deiconify()
        return shipper.strip()         

    def custom_askstring(self, title, prompt, bg_color):
        # Create a small window that is pinned to the top.
        dialog = Toplevel(self.root)
        dialog.title(title)
        
        # --- Centering logic begins---
        width  = 500
        height = 400
        
        # Get the screen resolution
        screen_width = dialog.winfo_screenwidth()
        screen_height = dialog.winfo_screenheight()
        
        # Formula for calculating center coordinates
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        
        """
         Set the window size and position: 
         width x height + left margin + top margin
        """
        dialog.geometry(f"{width}x{height}+{x}+{y}")

        # --- The centering logic ends ---
        dialog.configure(bg=bg_color)
        dialog.grab_set()

        result = {"value": ""}

        def on_confirm():
            result["value"] = entry.get()
            dialog.destroy()

        Label(dialog, text=prompt, bg=bg_color, font=("Arial", 12)).pack(pady=10)
        entry = Entry(dialog, font=("Arial", 14))
        entry.pack(pady=5)
        entry.focus_set()        
        entry.bind("<Return>", lambda e: on_confirm())
        Button(dialog, text="Confirm", command=on_confirm, width=10).pack(pady=10)

        self.root.wait_window(dialog)
        return result["value"]  # Return value for convenient use later.        