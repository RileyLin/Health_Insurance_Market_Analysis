import pandas as pd
import os
import re
from functools import lru_cache
import numpy as np

def clean_column_names(df):
    """Standardize column names"""
    df.columns = [re.sub(r'[^a-zA-Z0-9_]', '', col.lower().replace(' ', '_').replace('-', '_')) for col in df.columns]
    return df

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

def get_metal_level_colors():
    """Return a dictionary of metal level colors for consistent visualizations"""
    return {
        'Platinum': '#7E909A',
        'Gold': '#FFD700',
        'Silver': '#C0C0C0',
        'Bronze': '#CD7F32',
        'Catastrophic': '#E57373'
    }

def format_currency(value):
    """Format a value as currency"""
    return f"${value:,.2f}"

def format_percentage(value):
    """Format a value as percentage"""
    return f"{value:.1f}%"

def format_number(value):
    """Format a large number with commas"""
    try:
        # Ensure value is a number before formatting
        num_value = float(value) if not isinstance(value, (int, float)) else value
        if num_value.is_integer():
            return f"{int(num_value):,}"
        return f"{num_value:,.2f}"
    except (ValueError, AttributeError, TypeError):
        # If conversion fails, return the original value
        return str(value)

def detect_columns(df, keyword):
    """Find columns that contain a specific keyword"""
    if df.empty:
        return []
    return [col for col in df.columns if keyword.lower() in col.lower()]

def safe_divide(numerator, denominator):
    """Safely divide two numbers, returning 0 if denominator is 0"""
    if denominator == 0:
        return 0
    return numerator / denominator

def to_csv_name(excel_file):
    """Convert an Excel filename to CSV filename"""
    return excel_file.replace('.xlsx', '.csv')

def ensure_dir(directory):
    """Ensure a directory exists"""
    if not os.path.exists(directory):
        os.makedirs(directory)
        
def get_trend_emoji(current, previous):
    """Return an emoji indicating trend direction"""
    if current > previous:
        return "📈"  # Up
    elif current < previous:
        return "📉"  # Down
    else:
        return "➡️"  # Flat

def calculate_growth(current, previous):
    """Calculate percentage growth"""
    if previous == 0:
        return 0
    return ((current - previous) / previous) * 100

@lru_cache(maxsize=32)
def load_cached_data(file_path):
    """Load data with caching for performance"""
    if file_path.endswith('.csv'):
        return pd.read_csv(file_path)
    elif file_path.endswith('.xlsx'):
        return pd.read_excel(file_path)
    return pd.DataFrame()

def find_closest_columns(df, target_columns):
    """Find the closest matching columns in a dataframe
    
    Args:
        df: Pandas DataFrame
        target_columns: List of column names we're looking for
        
    Returns:
        Dictionary mapping target column names to actual column names
    """
    if df.empty:
        return {}
        
    result = {}
    for target in target_columns:
        # Try exact match first
        if target in df.columns:
            result[target] = target
            continue
            
        # Try case-insensitive match
        target_lower = target.lower()
        for col in df.columns:
            if col.lower() == target_lower:
                result[target] = col
                break
                
        # Try fuzzy match (contains)
        if target not in result:
            for col in df.columns:
                if target_lower in col.lower() or col.lower() in target_lower:
                    result[target] = col
                    break
                    
    return result

def get_top_n_states(df, metric_column, n=10, ascending=False):
    """Get the top N states by a specific metric"""
    if df.empty or 'state' not in df.columns or metric_column not in df.columns:
        return pd.DataFrame()
        
    return df.sort_values(metric_column, ascending=ascending).head(n) 