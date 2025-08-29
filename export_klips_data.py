import sqlite3
import csv
import os
from datetime import datetime

def export_klips_data_to_csv():
    """Export all data from klipps.db to a CSV file"""
    
    # Connect to the database
    conn = sqlite3.connect('klipps.db')
    cursor = conn.cursor()
    
    # Get all data from the extracted_images table
    cursor.execute("SELECT * FROM extracted_images")
    rows = cursor.fetchall()
    
    # Get column names
    cursor.execute("PRAGMA table_info(extracted_images)")
    columns = [column[1] for column in cursor.fetchall()]
    
    # Create CSV file
    csv_filename = f"klips_database_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        
        # Write header
        writer.writerow(columns)
        
        # Write data
        for row in rows:
            writer.writerow(row)
    
    conn.close()
    
    print(f"✅ Database exported to: {csv_filename}")
    print(f"📊 Total records exported: {len(rows)}")
    
    # Display sample data
    if rows:
        print("\n📋 Sample data:")
        print("Columns:", columns)
        print("First record:", rows[0])
    
    return csv_filename

if __name__ == "__main__":
    export_klips_data_to_csv() 