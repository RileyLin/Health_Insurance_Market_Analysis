import pandas as pd
import numpy as np

def calculate_kpis(df, metric_type):
    """Calculate key performance indicators based on the metric type"""
    if df.empty:
        return 0
    
    if metric_type == 'total_enrollments':
        # Sum total enrollments across all states
        if 'total_enrollments' in df.columns:
            try:
                return pd.to_numeric(df['total_enrollments'], errors='coerce').sum()
            except:
                return 0
        elif 'total_enrollment' in df.columns:
            try:
                return pd.to_numeric(df['total_enrollment'], errors='coerce').sum()
            except:
                return 0
        return 0
    
    elif metric_type == 'avg_premium':
        # Calculate average premium
        if 'average_premium' in df.columns:
            try:
                return pd.to_numeric(df['average_premium'], errors='coerce').mean()
            except:
                return 0
        elif 'avg_premium' in df.columns:
            try:
                return pd.to_numeric(df['avg_premium'], errors='coerce').mean()
            except:
                return 0
        return 0
    
    elif metric_type == 'pct_with_aptc':
        # Calculate percentage with Advanced Premium Tax Credit
        if 'consumers_with_aptc' in df.columns and 'total_enrollments' in df.columns:
            try:
                total_consumers = pd.to_numeric(df['total_enrollments'], errors='coerce').sum()
                consumers_with_aptc = pd.to_numeric(df['consumers_with_aptc'], errors='coerce').sum()
                if total_consumers > 0:
                    return 100 * consumers_with_aptc / total_consumers
            except:
                return 0
        elif 'pct_with_aptc' in df.columns:
            try:
                return pd.to_numeric(df['pct_with_aptc'], errors='coerce').mean()
            except:
                return 0
        return 0
    
    return 0

def calculate_enrollment_growth(historical_df):
    """Calculate year-over-year enrollment growth rates"""
    if historical_df.empty:
        return pd.Series()
    
    # Identify year column
    year_col = next((col for col in historical_df.columns if 'year' in col.lower()), None)
    enrollment_col = next((col for col in historical_df.columns if 'enrollment' in col.lower()), None)
    
    if not year_col or not enrollment_col:
        return pd.Series()
    
    # Group by year and calculate totals
    # Convert to numeric before calculations
    try:
        historical_df[enrollment_col] = pd.to_numeric(historical_df[enrollment_col], errors='coerce')
        yearly_totals = historical_df.groupby(year_col)[enrollment_col].sum()
        
        # Calculate growth rates
        growth_rates = yearly_totals.pct_change() * 100
        
        return growth_rates
    except:
        return pd.Series()

def calculate_market_penetration(state_df, population_data=None):
    """
    Calculate market penetration index using enrollment data and population
    
    If population_data is not provided, we'll use relative penetration based on total enrollments
    """
    if state_df.empty:
        return pd.DataFrame()
    
    result_df = state_df.copy()
    
    # Convert columns to numeric if needed
    if 'total_enrollments' in result_df.columns:
        result_df['total_enrollments'] = pd.to_numeric(result_df['total_enrollments'], errors='coerce')
    
    # If we have population data, calculate actual penetration rates
    if population_data is not None and not population_data.empty:
        result_df = result_df.merge(population_data, on='state', how='left')
        population_data['population'] = pd.to_numeric(population_data['population'], errors='coerce')
        result_df['penetration_rate'] = result_df['total_enrollments'] / result_df['population'] * 100
    else:
        # Otherwise, calculate normalized penetration (as % of max enrollment)
        max_enrollment = result_df['total_enrollments'].max()
        if max_enrollment > 0:
            result_df['relative_penetration'] = result_df['total_enrollments'] / max_enrollment * 100
    
    return result_df

def calculate_premium_affordability(state_df, income_data=None):
    """
    Calculate premium affordability score based on premiums vs. income
    
    Lower scores indicate more affordable premiums relative to income
    """
    if state_df.empty:
        return pd.DataFrame()
    
    result_df = state_df.copy()
    
    # Convert columns to numeric if needed
    if 'average_premium' in result_df.columns:
        result_df['average_premium'] = pd.to_numeric(result_df['average_premium'], errors='coerce')
    
    # If we have income data, use it for actual affordability calculation
    if income_data is not None and not income_data.empty:
        result_df = result_df.merge(income_data, on='state', how='left')
        income_data['median_income'] = pd.to_numeric(income_data['median_income'], errors='coerce')
        result_df['affordability_score'] = result_df['average_premium'] / result_df['median_income'] * 1000
    else:
        # Otherwise, normalize premiums by the lowest premium state (higher = less affordable)
        min_premium = result_df['average_premium'].min()
        if min_premium > 0:
            result_df['affordability_index'] = result_df['average_premium'] / min_premium
    
    return result_df

def calculate_plan_value_metric(plan_df):
    """
    Design a Plan Value Metric comparing metal levels to actual benefits
    
    This is a simplified version assuming we have deductible and MOOP data
    """
    if plan_df.empty:
        return pd.DataFrame()
    
    result_df = plan_df.copy()
    
    # Try to find relevant columns
    metal_col = next((col for col in result_df.columns if 'metal' in col.lower()), None)
    deductible_col = next((col for col in result_df.columns if 'deductible' in col.lower()), None)
    moop_col = next((col for col in result_df.columns if 'maximum_out_of_pocket' in col.lower() or 'moop' in col.lower()), None)
    premium_col = next((col for col in result_df.columns if 'premium' in col.lower()), None)
    
    # If we don't have the necessary data, return the original dataframe
    if not all([metal_col, deductible_col, premium_col]):
        return result_df
    
    # Convert columns to numeric if needed
    for col in [deductible_col, moop_col, premium_col]:
        if col in result_df.columns:
            result_df[col] = pd.to_numeric(result_df[col], errors='coerce')
    
    # Normalize each component inversely (lower deductible/MOOP is better)
    if deductible_col:
        max_deductible = result_df[deductible_col].max()
        if max_deductible > 0:
            result_df['deductible_score'] = 1 - (result_df[deductible_col] / max_deductible)
    
    if moop_col:
        max_moop = result_df[moop_col].max()
        if max_moop > 0:
            result_df['moop_score'] = 1 - (result_df[moop_col] / max_moop)
    
    # Create a composite score
    score_columns = [col for col in ['deductible_score', 'moop_score'] if col in result_df.columns]
    if score_columns:
        result_df['plan_value_score'] = result_df[score_columns].mean(axis=1)
    
    return result_df 