import pandas as pd
from io import BytesIO

def to_excel(data_dict):
    """
    Converts a dictionary of extracted data to an Excel file in memory.
    Returns the Excel file as bytes.
    """
    # Create a DataFrame
    # We want columns: Title, Authors, Abstract, Introduction, ...
    df = pd.DataFrame([data_dict])
    
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Extracted Data')
        
        # Auto-adjust column width (optional, basic estimation)
        worksheet = writer.sheets['Extracted Data']
        for column_cells in worksheet.columns:
            length = max(len(str(cell.value)) for cell in column_cells)
            # Cap width at 50 to avoid huge columns
            worksheet.column_dimensions[column_cells[0].column_letter].width = min(length + 2, 50)
            
    return output.getvalue()
