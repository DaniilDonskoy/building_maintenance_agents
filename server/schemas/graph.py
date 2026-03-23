from pydantic import BaseModel


class GraphParams(BaseModel):
	
	# Example:
 
	# floors = 15
    # sections = 2
    # flats_per_section = 3
    # elevs_per_section = 1
	
    ...
    

class GraphType(BaseModel):
    
    # Example: House15Factory
    
    ...