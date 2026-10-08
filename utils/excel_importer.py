# -*- coding: utf-8 -*-
# utils/excel_importer.py
import sys
import os
import logging
import pandas as pd

_log = logging.getLogger("ExcelImporter")

class ExcelImporter:
    """
    Robust Excel importer utility for reading official or custom lotto draw records 
    and harmonizing column schemas with the local database structure.
    """
    @staticmethod
    def import_draws_from_excel(file_path: str) -> list:
        """
        Reads an Excel file and returns a list of standardized draw dictionaries.
        """
        try:
            if not os.path.exists(file_path):
                _log.error(f"Excel file not found at: {file_path}")
                return []

            df = pd.read_excel(file_path)
            if df.empty:
                _log.warning("The provided Excel file is empty.")
                return []

            draws = []
            for _, row in df.iterrows():
                draw_data = {}
                
                # Round column mapping search
                round_val = 0
                for col in ['drwNo', 'draw_no', 'Round', 'round']:
                    if col in df.columns and pd.notnull(row[col]):
                        try:
                            round_val = int(row[col])
                            break
                        except ValueError:
                            pass
                if round_val <= 0:
                    continue
                
                draw_data['draw_no'] = round_val

                # Date column mapping search
                date_val = "-"
                for col in ['drwNoDate', 'draw_date', 'Date', 'date']:
                    if col in df.columns and pd.notnull(row[col]):
                        date_val = str(row[col]).strip()
                        break
                draw_data['draw_date'] = date_val

                # Numbers (N1~N6) mapping
                numbers = []
                for i in range(1, 7):
                    num_val = 0
                    for col in [f'num{i}', f'drwtNo{i}', f'Number{i}', f'n{i}']:
                        if col in df.columns and pd.notnull(row[col]):
                            try:
                                num_val = int(row[col])
                                break
                            except ValueError:
                                pass
                    numbers.append(num_val)

                for i, num in enumerate(numbers, start=1):
                    draw_data[f'num{i}'] = num

                # Bonus number mapping
                bonus_val = 0
                for col in ['bonus', 'bnusNo', 'Bonus']:
                    if col in df.columns and pd.notnull(row[col]):
                        try:
                            bonus_val = int(row[col])
                            break
                        except ValueError:
                            pass
                draw_data['bonus'] = bonus_val

                # Total sales and prize info mapping
                sales_val = 0
                for col in ['tot_sellamnt', 'totSellamnt', 'sales']:
                    if col in df.columns and pd.notnull(row[col]):
                        try:
                            sales_val = int(str(row[col]).replace(',', '').replace('KRW', '').strip())
                            break
                        except ValueError:
                            pass
                draw_data['tot_sellamnt'] = sales_val

                draws.append(draw_data)

            _log.info(f"Successfully imported {len(draws)} records from Excel: {file_path}")
            return draws

        except Exception as e:
            _log.error(f"Failed to import Excel file {file_path}: {e}")
            return []