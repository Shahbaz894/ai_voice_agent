from __future__ import annotations
from sqlalchemy import text
from database import engine,init_db

def run_sql(query:str):
    """_summary_

    Args:
        query (str): _description_

    Returns:
        _type_: _description_
    """
    
    
    with engine.begin() as conn:
        result=conn.execute(text(query))
        return result.fetchall() if result.returns_rows else result.rowcount
    
    
query="SELECT * FROM appointments"
# query = """
# INSERT INTO appointments 
# (patient_name, reason, start_time, canceled, created_at) 
# VALUES 
# ('John Doe', 'Annual Checkup', '2024-01-15 10:00:00', 0, '2024-01-15 10:00:00')
# """

print(run_sql(query))