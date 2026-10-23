class AppError(Exception):
    status_code = 400
    
class ExcelFormatError(AppError):
    status_code = 400
  
class FileLockedError(AppError):
    status_code = 409  

class NegativeError(AppError):     
    status_code = 400
    
class NoneListError(AppError):
    status_code =404
  
class NoItemError(AppError):
    status_code = 404

class UrlError(AppError):
    status_code = 404
       
class StockShortError(AppError):
    status_code = 409    

class UnknownError(AppError):
    status_code = 500    

class NameLackError(AppError):
    status_code = 400
   
class FileInuseError(AppError):
    status_code = 409

class UnProcessError(AppError):
    status_code = 422
    
class ReadError(AppError):
    status_code = 500 
   
class WriteError(AppError):
    status_code = 500  
  
