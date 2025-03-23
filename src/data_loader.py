import pandas as pd
import os
import numpy as np

def load_state_data():
    """Load and clean state-level OEP data"""
    try:
        print("Loading state data...")
        df = pd.read_csv('data/2024 OEP State-Level Public Use File.csv')
        
        # Handle columns with special characters and standardize names
        df.columns = [col.lower().replace(' ', '_').replace('-', '_') for col in df.columns]
        
        print(f"Original columns: {df.columns.tolist()}")
        
        # Create direct mapping for critical columns
        if 'cnsmr' in df.columns:
            # Convert to numeric right away
            df['cnsmr'] = pd.to_numeric(df['cnsmr'].str.replace(',', ''), errors='coerce')
            df['total_enrollments'] = df['cnsmr']
            print(f"Mapped 'cnsmr' to 'total_enrollments', first few values: {df['total_enrollments'].head().tolist()}")
        
        # Map key columns to expected names in the application
        column_mapping = {
            'state_abrvtn': 'state_code',
            'new_cnsmr': 'new_enrollments',
            'avg_prm': 'average_premium',
            'avg_prm_aftr_aptc': 'average_premium_after_aptc',
            'aptc_cnsmr': 'consumers_with_aptc',
            'aptc_cnsmr_avg_aptc': 'average_aptc'
        }
        
        # Rename columns if they exist
        for old_col, new_col in column_mapping.items():
            if old_col in df.columns:
                # Convert to numeric for known numeric columns
                if old_col == 'avg_prm' or old_col == 'avg_prm_aftr_aptc' or old_col == 'aptc_cnsmr_avg_aptc':
                    try:
                        df[old_col] = df[old_col].astype(str).str.replace('$', '').str.replace(',', '')
                        df[old_col] = pd.to_numeric(df[old_col], errors='coerce')
                    except:
                        pass
                elif old_col == 'new_cnsmr' or old_col == 'aptc_cnsmr':
                    try:
                        df[old_col] = df[old_col].astype(str).str.replace(',', '')
                        df[old_col] = pd.to_numeric(df[old_col], errors='coerce')
                    except:
                        pass
                
                df[new_col] = df[old_col]
        
        # Process common demographics columns
        demographic_cols = {
            'male': 'male',
            'female': 'female',
            'age_0_17': 'age_0_17',
            'age_18_25': 'age_18_25',
            'age_26_34': 'age_26_34',
            'age_35_44': 'age_35_44',
            'age_45_54': 'age_45_54',
            'age_55_64': 'age_55_64',
            'age_ge65': 'age_over_65',
            'rrl': 'rural',
            'non_rrl': 'non_rural'
        }
        
        for old_col, new_col in demographic_cols.items():
            if old_col in df.columns:
                try:
                    df[old_col] = df[old_col].astype(str).str.replace(',', '')
                    df[old_col] = pd.to_numeric(df[old_col], errors='coerce')
                    df[new_col] = df[old_col]
                except:
                    pass
        
        # Process metal level columns
        metal_cols = {
            'brnz': 'bronze',
            'slvr': 'silver',
            'gld': 'gold',
            'pltnm': 'platinum',
            'ctstrphc': 'catastrophic'
        }
        
        for old_col, new_col in metal_cols.items():
            if old_col in df.columns:
                try:
                    df[old_col] = df[old_col].astype(str).str.replace(',', '')
                    df[old_col] = pd.to_numeric(df[old_col], errors='coerce')
                    df[new_col] = df[old_col]
                except:
                    pass
                
        # Add metal level type column for charts
        if all(col in df.columns for col in ['bronze', 'silver', 'gold', 'platinum', 'catastrophic']):
            # Create a DataFrame for metal level data
            metal_data = []
            for state in df['state_code'].unique():
                state_data = df[df['state_code'] == state]
                for metal, col in zip(['Bronze', 'Silver', 'Gold', 'Platinum', 'Catastrophic'], 
                                     ['bronze', 'silver', 'gold', 'platinum', 'catastrophic']):
                    if col in state_data.columns:
                        value = state_data[col].iloc[0]
                        if pd.notna(value) and value > 0:
                            metal_data.append({
                                'state': state,
                                'metal_level': metal,
                                'enrollment': value
                            })
            if metal_data:
                metal_df = pd.DataFrame(metal_data)
                # Merge with main DataFrame
                df = pd.merge(df, metal_df, left_on='state_code', right_on='state', how='left')
        
        # Convert numeric columns and handle special values
        for col in df.columns:
            # Skip non-numeric columns
            if col in ['state_code', 'state', 'county', 'fips', 'pltfrm', 'metal_level']:
                continue
                
            # Handle special values first
            df[col] = df[col].replace('NR', np.nan)
            df[col] = df[col].replace('+', np.nan)
            
            # Handle dollar amounts and other numeric values
            if df[col].dtype == 'object':
                try:
                    # Remove $ and commas if present
                    if df[col].astype(str).str.contains('\$').any():
                        df[col] = df[col].astype(str).str.replace('$', '').str.replace(',', '')
                    elif df[col].astype(str).str.contains(',').any():
                        df[col] = df[col].astype(str).str.replace(',', '')
                    
                    # Then convert to numeric
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                except:
                    # If conversion fails, keep the column as is
                    pass
        
        # Make sure we have state_code and state columns - critical for geographic analysis
        if 'state_code' in df.columns and 'state' not in df.columns:
            # Set state to state_code if we don't have state column
            df['state'] = df['state_code']
            print(f"Created 'state' column from 'state_code': {df['state'].head().tolist()}")
        
        # Handle missing values for numeric columns
        df = df.fillna(0)
        
        print(f"Processed columns: {df.columns.tolist()}")
        print(f"Data shape: {df.shape}")
        print(f"Sample state codes: {df['state_code'].head().tolist()}")
        if 'state' in df.columns:
            print(f"Sample state names: {df['state'].head().tolist()}")
        print(f"Sample total_enrollments: {df['total_enrollments'].head().tolist()}")
        
        return df
    except Exception as e:
        print(f"Error loading state data: {e}")
        import traceback
        traceback.print_exc()
        # Return empty DataFrame with expected columns if file not found
        return pd.DataFrame()

def load_county_data():
    """Load and clean county-level OEP data"""
    try:
        print("Loading county data...")
        df = pd.read_csv('data/2024 OEP County-Level Public Use File.csv')
        
        # Handle columns with special characters and standardize names
        df.columns = [col.lower().replace(' ', '_').replace('-', '_') for col in df.columns]
        
        print(f"Original county columns: {df.columns.tolist()}")
        
        # Create direct mapping for critical columns
        if 'cnsmr' in df.columns:
            # Convert to numeric right away
            df['cnsmr'] = pd.to_numeric(df['cnsmr'].str.replace(',', ''), errors='coerce')
            df['total_enrollments'] = df['cnsmr']
            print(f"County data: Mapped 'cnsmr' to 'total_enrollments', first few values: {df['total_enrollments'].head().tolist()}")
        
        # Map key columns to expected names
        column_mapping = {
            'state_abrvtn': 'state_code',
            'county_fips_cd': 'fips',
            'new_cnsmr': 'new_enrollments',
            'avg_prm': 'average_premium',
            'avg_prm_aftr_aptc': 'average_premium_after_aptc',
        }
        
        # Rename columns if they exist
        for old_col, new_col in column_mapping.items():
            if old_col in df.columns:
                # Convert to numeric for known numeric columns
                if old_col == 'avg_prm' or old_col == 'avg_prm_aftr_aptc':
                    try:
                        df[old_col] = df[old_col].astype(str).str.replace('$', '').str.replace(',', '')
                        df[old_col] = pd.to_numeric(df[old_col], errors='coerce')
                    except:
                        pass
                elif old_col == 'new_cnsmr':
                    try:
                        df[old_col] = df[old_col].astype(str).str.replace(',', '')
                        df[old_col] = pd.to_numeric(df[old_col], errors='coerce')
                    except:
                        pass
                    
                df[new_col] = df[old_col]
        
        # If we have a county name column, standardize it
        county_name_cols = ['county_name', 'county_nm', 'county']
        for col in county_name_cols:
            if col in df.columns:
                df['county'] = df[col]
                break
        
        # If we don't have county column, use FIPS code as county name
        if 'county' not in df.columns and 'fips' in df.columns:
            df['county'] = df['fips'].astype(str)
            print(f"Created 'county' column from 'fips': {df['county'].head().tolist()}")
            
        # Make sure we have state column
        if 'state_code' in df.columns and 'state' not in df.columns:
            df['state'] = df['state_code']
            print(f"Created 'state' column from 'state_code': {df['state'].head().tolist()}")
        
        # Convert numeric columns and handle special values
        for col in df.columns:
            # Skip non-numeric columns
            if col in ['state_code', 'state', 'county', 'fips']:
                continue
                
            # Handle special values first
            df[col] = df[col].replace('NR', np.nan)
            df[col] = df[col].replace('+', np.nan)
            
            # Handle dollar amounts and other numeric values
            if df[col].dtype == 'object':
                try:
                    # Remove $ and commas if present
                    if df[col].astype(str).str.contains('\$').any():
                        df[col] = df[col].astype(str).str.replace('$', '').str.replace(',', '')
                    elif df[col].astype(str).str.contains(',').any():
                        df[col] = df[col].astype(str).str.replace(',', '')
                    
                    # Then convert to numeric
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                except:
                    # If conversion fails, keep the column as is
                    pass

        # Handle missing values for numeric columns
        df = df.fillna(0)
        
        print(f"Processed county columns: {df.columns.tolist()}")
        print(f"County data shape: {df.shape}")
        print(f"Sample county state codes: {df['state_code'].head().tolist()}")
        if 'state' in df.columns:
            print(f"Sample county states: {df['state'].head().tolist()}")
        print(f"Sample county FIPS: {df['fips'].head().tolist()}")
        
        return df
    except Exception as e:
        print(f"Error loading county data: {e}")
        import traceback
        traceback.print_exc()
        # Return empty DataFrame with expected columns if file not found
        return pd.DataFrame()

def load_historical_data():
    """Load and clean historical plan design data"""
    try:
        print("Loading historical data...")
        # Try to load CSV first
        file_path = 'data/2014-2024 OEP Plan Design Public Use File.csv'
        if not os.path.exists(file_path):
            # If CSV doesn't exist, try to load Excel and convert
            excel_path = 'data/2014-2024 OEP Plan Design Public Use File.xlsx'
            if os.path.exists(excel_path):
                df = pd.read_excel(excel_path)
                # Optionally save as CSV for future use
                # df.to_csv(file_path, index=False)
            else:
                raise FileNotFoundError(f"Neither {file_path} nor {excel_path} could be found")
        else:
            df = pd.read_csv(file_path)
        
        # Data cleaning and transformations
        df.columns = [col.lower().replace(' ', '_').replace('-', '_') for col in df.columns]
        
        # Convert numeric columns and handle special values
        for col in df.columns:
            # Skip non-numeric columns
            if col in ['state_code', 'state', 'county', 'fips', 'year']:
                continue
                
            # Handle special values first
            df[col] = df[col].replace('NR', np.nan)
            df[col] = df[col].replace('+', np.nan)
            
            # Handle dollar amounts and other numeric values
            if df[col].dtype == 'object':
                try:
                    # Remove $ and commas if present
                    if df[col].astype(str).str.contains('\$').any():
                        df[col] = df[col].astype(str).str.replace('$', '').str.replace(',', '')
                    
                    # Then convert to numeric
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                except:
                    # If conversion fails, keep the column as is
                    pass
        
        # Handle missing values for numeric columns
        df = df.fillna(0)
        
        print(f"Historical data shape: {df.shape}")
        
        return df
    except Exception as e:
        print(f"Error loading historical data: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()

def convert_excel_to_csv():
    """Convert Excel files to CSV for faster loading"""
    excel_files = [
        ('data/2024 OEP State-Level Public Use File.xlsx', 'data/2024 OEP State-Level Public Use File.csv'),
        ('data/2024 OEP County-Level Public Use File.xlsx', 'data/2024 OEP County-Level Public Use File.csv'),
        ('data/2014-2024 OEP Plan Design Public Use File.xlsx', 'data/2014-2024 OEP Plan Design Public Use File.csv')
    ]
    
    for excel_path, csv_path in excel_files:
        if os.path.exists(excel_path) and not os.path.exists(csv_path):
            try:
                df = pd.read_excel(excel_path)
                df.to_csv(csv_path, index=False)
                print(f"Converted {excel_path} to {csv_path}")
            except Exception as e:
                print(f"Error converting {excel_path} to CSV: {e}")

def get_state_mapping():
    """Return a dictionary mapping state names to state codes"""
    state_mapping = {
        'Alabama': 'AL', 'Alaska': 'AK', 'Arizona': 'AZ', 'Arkansas': 'AR', 'California': 'CA',
        'Colorado': 'CO', 'Connecticut': 'CT', 'Delaware': 'DE', 'Florida': 'FL', 'Georgia': 'GA',
        'Hawaii': 'HI', 'Idaho': 'ID', 'Illinois': 'IL', 'Indiana': 'IN', 'Iowa': 'IA',
        'Kansas': 'KS', 'Kentucky': 'KY', 'Louisiana': 'LA', 'Maine': 'ME', 'Maryland': 'MD',
        'Massachusetts': 'MA', 'Michigan': 'MI', 'Minnesota': 'MN', 'Mississippi': 'MS', 'Missouri': 'MO',
        'Montana': 'MT', 'Nebraska': 'NE', 'Nevada': 'NV', 'New Hampshire': 'NH', 'New Jersey': 'NJ',
        'New Mexico': 'NM', 'New York': 'NY', 'North Carolina': 'NC', 'North Dakota': 'ND', 'Ohio': 'OH',
        'Oklahoma': 'OK', 'Oregon': 'OR', 'Pennsylvania': 'PA', 'Rhode Island': 'RI', 'South Carolina': 'SC',
        'South Dakota': 'SD', 'Tennessee': 'TN', 'Texas': 'TX', 'Utah': 'UT', 'Vermont': 'VT',
        'Virginia': 'VA', 'Washington': 'WA', 'West Virginia': 'WV', 'Wisconsin': 'WI', 'Wyoming': 'WY',
        'District of Columbia': 'DC'
    }
    return state_mapping 