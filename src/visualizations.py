import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

def create_map(df, value_column, title, hover_data=None):
    """Create choropleth map of US states"""
    if df.empty:
        print("create_map: DataFrame is empty")
        return go.Figure()
        
    # Identify state code column
    state_code_col = next((col for col in df.columns if 'state_code' in col.lower() or 'state_abbrev' in col.lower()), None)
    state_name_col = next((col for col in df.columns if col.lower() == 'state'), None)
    
    if not state_code_col:
        print("create_map: No state code column found")
        return go.Figure()
    
    # Debug info
    print(f"create_map: state_code_col={state_code_col}, state_name_col={state_name_col}, value_column={value_column}")
    print(f"create_map: Sample state codes: {df[state_code_col].head().tolist()}")
    
    # Ensure state_code is uppercase for mapping
    df = df.copy()
    df[state_code_col] = df[state_code_col].astype(str).str.upper()
    
    # Convert value column to numeric if it's not already
    try:
        df[value_column] = pd.to_numeric(df[value_column], errors='coerce')
        print(f"create_map: Sample values: {df[value_column].head().tolist()}")
    except Exception as e:
        print(f"create_map: Error converting {value_column} to numeric: {e}")
        pass
    
    # Define default hover data if none provided
    if hover_data is None:
        hover_data = {
            state_code_col: False
        }
        
        # Add value column to hover
        if value_column:
            hover_data[value_column] = True
            
        # Add enrollment data to hover if available
        enrollment_col = next((col for col in df.columns if 'enrollment' in col.lower()), None)
        if enrollment_col and enrollment_col != value_column:
            hover_data[enrollment_col] = True
            
        # Add premium data to hover if available
        premium_col = next((col for col in df.columns if 'premium' in col.lower()), None)
        if premium_col and premium_col != value_column:
            hover_data[premium_col] = True
    
    # Create the hover_name for the map
    if state_name_col:
        hover_name = state_name_col
    else:
        # If no state name column, use state code for hover
        hover_name = state_code_col
        
    try:
        fig = px.choropleth(
            df,
            locations=state_code_col,
            locationmode="USA-states",
            color=value_column,
            scope="usa",
            color_continuous_scale="Blues",
            title=title,
            hover_name=hover_name,
            hover_data=hover_data
        )
        fig.update_layout(margin={"r":0,"t":30,"l":0,"b":0})
        return fig
    except Exception as e:
        print(f"create_map: Error creating choropleth map: {e}")
        import traceback
        traceback.print_exc()
        # Return empty figure
        return go.Figure()

def create_premium_chart(df, state_filter=None, year_column=None, premium_column=None):
    """Create line chart for premium trends"""
    if df.empty:
        return go.Figure()
    
    # Filter by state if specified
    if state_filter and 'state' in df.columns:
        df = df[df['state'] == state_filter]
    
    # Identify columns if not provided
    if not year_column:
        year_column = next((col for col in df.columns if 'year' in col.lower()), None)
    if not premium_column:
        premium_column = next((col for col in df.columns if 'premium' in col.lower()), None)
    
    if not year_column or not premium_column or year_column not in df.columns or premium_column not in df.columns:
        return go.Figure()
    
    # Convert premium column to numeric if it's not already
    try:
        df[premium_column] = pd.to_numeric(df[premium_column], errors='coerce')
    except:
        pass
    
    # Create chart
    fig = px.line(
        df, 
        x=year_column, 
        y=premium_column,
        title=f"Premium Trends{' for '+state_filter if state_filter else ''}",
        markers=True
    )
    
    fig.update_layout(
        xaxis_title="Year",
        yaxis_title="Average Premium ($)",
        hovermode="x unified"
    )
    
    return fig

def create_demographic_chart(df, demographic_column, title=None):
    """Create demographic breakdown charts"""
    if df.empty:
        return go.Figure()
    
    # Special case for age group data which is spread across multiple columns
    if demographic_column == 'age':
        # Find all age columns
        age_cols = [col for col in df.columns if col.startswith('age_') or col == 'age_over_65']
        if not age_cols:
            return go.Figure()
        
        print(f"Found age columns: {age_cols}")
        
        # Create a new dataframe with age data
        age_data = []
        for col in age_cols:
            # Clean up the age group name
            age_name = col.replace('age_', '').replace('_', '-').upper()
            if age_name == 'GE65' or age_name == 'OVER-65':
                age_name = '65+'
                
            # Sum the values for this age group across all states
            total = df[col].sum()
            if total > 0:
                age_data.append({
                    'age_group': age_name,
                    'enrollment': total
                })
        
        if not age_data:
            return go.Figure()
            
        # Create dataframe and sort by age group logically
        age_df = pd.DataFrame(age_data)
        
        # Define custom sort order
        age_order = ['0-17', '18-25', '26-34', '35-44', '45-54', '55-64', '65+']
        
        # Map age groups to their sort order
        sort_map = {age: i for i, age in enumerate(age_order)}
        
        # Sort by the defined order
        age_df['sort_order'] = age_df['age_group'].map(lambda x: sort_map.get(x, 999))
        age_df = age_df.sort_values('sort_order')
        
        # Create horizontal bar chart
        fig = px.bar(
            age_df,
            y='age_group',
            x='enrollment',
            orientation='h',
            title=title or "Enrollment by Age Group",
            text='enrollment'
        )
        
        fig.update_layout(
            xaxis_title="Enrollment",
            yaxis_title="Age Group",
            yaxis={'categoryorder':'array', 'categoryarray':age_df['age_group']}
        )
        
        # Format text labels
        fig.update_traces(texttemplate='%{text:,}', textposition='outside')
        
        return fig
        
    # Special case for gender data which is spread across multiple columns
    elif demographic_column == 'gender':
        # Find gender columns
        gender_cols = [col for col in df.columns if col.lower() in ['male', 'female']]
        if not gender_cols:
            return go.Figure()
            
        print(f"Found gender columns: {gender_cols}")
        
        # Create a new dataframe with gender data
        gender_data = []
        for col in gender_cols:
            total = df[col].sum()
            if total > 0:
                gender_data.append({
                    'gender': col.title(),
                    'enrollment': total
                })
        
        if not gender_data:
            return go.Figure()
            
        gender_df = pd.DataFrame(gender_data)
        
        # Create pie chart for gender
        fig = px.pie(
            gender_df,
            values='enrollment',
            names='gender',
            title=title or "Enrollment by Gender",
            hole=0.4
        )
        
        # Improve formatting
        fig.update_traces(textposition='inside', textinfo='percent+label')
        
        return fig
        
    # Special case for income level data
    elif demographic_column == 'income':
        # Find FPL columns (Federal Poverty Level)
        fpl_cols = [col for col in df.columns if col.startswith('fpl_')]
        if not fpl_cols:
            return go.Figure()
            
        print(f"Found income level columns: {fpl_cols}")
        
        # Create a new dataframe with income data
        income_data = []
        for col in fpl_cols:
            # Clean up the income level name
            income_name = col.replace('fpl_', '').replace('_', '-').upper()
            
            # Make income levels more readable
            if income_name == 'LT100':
                income_name = '<100% FPL'
            elif income_name == 'GT500':
                income_name = '>500% FPL'
            elif 'FPL' not in income_name:
                income_name = f"{income_name}% FPL"
                
            # Sum the values for this income level across all states
            total = df[col].sum()
            if total > 0:
                income_data.append({
                    'income_level': income_name,
                    'enrollment': total
                })
        
        if not income_data:
            return go.Figure()
            
        # Create dataframe and define sort order
        income_df = pd.DataFrame(income_data)
        
        # First, try to sort by extracting the numeric value
        try:
            # Extract numeric values for proper sorting
            income_df['sort_val'] = income_df['income_level'].str.extract(r'(\d+)').astype(float)
            income_df = income_df.sort_values('sort_val')
        except:
            # If that fails, sort alphabetically
            income_df = income_df.sort_values('income_level')
        
        # Create horizontal bar chart
        fig = px.bar(
            income_df,
            y='income_level',
            x='enrollment',
            orientation='h',
            title=title or "Enrollment by Income Level",
            text='enrollment'
        )
        
        fig.update_layout(
            xaxis_title="Enrollment",
            yaxis_title="Income Level"
        )
        
        # Format text labels
        fig.update_traces(texttemplate='%{text:,}', textposition='outside')
        
        return fig
        
    # Special case for consumer type (new vs returning)
    elif demographic_column == 'consumer_type':
        # Find relevant columns
        consumer_cols = {
            'new_enrollments': 'New',
            'tot_renrl': 'Returning'
        }
        
        found_cols = [col for col, label in consumer_cols.items() if col in df.columns]
        if not found_cols:
            return go.Figure()
            
        print(f"Found consumer type columns: {found_cols}")
        
        # Create a new dataframe with consumer type data
        consumer_data = []
        for col, label in consumer_cols.items():
            if col in df.columns:
                total = df[col].sum()
                if total > 0:
                    consumer_data.append({
                        'consumer_type': label,
                        'enrollment': total
                    })
        
        if not consumer_data:
            return go.Figure()
            
        consumer_df = pd.DataFrame(consumer_data)
        
        # Create horizontal bar chart
        fig = px.bar(
            consumer_df,
            y='consumer_type',
            x='enrollment',
            orientation='h',
            title=title or "New vs. Returning Consumers",
            text='enrollment',
            color='consumer_type',
            color_discrete_map={
                'New': '#1E88E5',
                'Returning': '#4CAF50'
            }
        )
        
        fig.update_layout(
            xaxis_title="Enrollment",
            yaxis_title="Consumer Type"
        )
        
        # Format text labels
        fig.update_traces(texttemplate='%{text:,}', textposition='outside')
        
        return fig
    
    # For standard demographic columns
    else:
        # Find enrollment column
        enrollment_col = next((col for col in df.columns if 'enrollment' in col.lower()), None)
        if not enrollment_col:
            enrollment_col = 'total_enrollments'
            if enrollment_col not in df.columns:
                return go.Figure()
        
        # Check if the demographic column exists
        if demographic_column not in df.columns:
            return go.Figure()
        
        # Convert enrollment column to numeric
        try:
            df[enrollment_col] = pd.to_numeric(df[enrollment_col], errors='coerce')
        except:
            pass
        
        # Group by demographic column
        grouped_df = df.groupby(demographic_column)[enrollment_col].sum().reset_index()
        
        # Sort by enrollment count (descending)
        grouped_df = grouped_df.sort_values(enrollment_col, ascending=False)
        
        # Generate chart title if not provided
        if not title:
            title = f"Enrollment by {demographic_column.replace('_', ' ').title()}"
        
        # Create horizontal bar chart
        fig = px.bar(
            grouped_df,
            y=demographic_column,
            x=enrollment_col,
            orientation='h',
            title=title,
            text=enrollment_col
        )
        
        fig.update_layout(
            xaxis_title="Enrollment",
            yaxis_title=demographic_column.replace('_', ' ').title()
        )
        
        # Format text labels
        fig.update_traces(texttemplate='%{text:,}', textposition='outside')
        
        return fig

def create_metal_level_chart(df, metal_level_column=None, year_column=None):
    """Create donut chart showing metal level distribution"""
    if df.empty:
        return go.Figure()
    
    # Identify columns if not provided
    if not metal_level_column:
        metal_level_column = next((col for col in df.columns if 'metal' in col.lower()), None)
    if not year_column and 'year' in df.columns:
        year_column = 'year'
        
    enrollment_col = next((col for col in df.columns if 'enrollment' in col.lower()), None)
    
    if not metal_level_column or not enrollment_col:
        return go.Figure()
    
    # Convert enrollment column to numeric
    try:
        df[enrollment_col] = pd.to_numeric(df[enrollment_col], errors='coerce')
    except:
        pass
    
    # Group by metal level
    group_cols = [metal_level_column]
    if year_column:
        group_cols.append(year_column)
        
    grouped_df = df.groupby(group_cols)[enrollment_col].sum().reset_index()
    
    # If we have year data, filter to most recent year
    if year_column and year_column in grouped_df.columns:
        max_year = grouped_df[year_column].max()
        grouped_df = grouped_df[grouped_df[year_column] == max_year]
    
    # Create donut chart
    fig = px.pie(
        grouped_df, 
        values=enrollment_col, 
        names=metal_level_column,
        title="Enrollment by Metal Level",
        hole=0.4,
        color=metal_level_column,
        color_discrete_map={
            'Platinum': '#7E909A',
            'Gold': '#FFD700',
            'Silver': '#C0C0C0',
            'Bronze': '#CD7F32',
            'Catastrophic': '#E57373'
        }
    )
    
    # Improve formatting
    fig.update_traces(textposition='inside', textinfo='percent+label')
    
    return fig

def create_state_comparison_chart(df, selected_states, metric_column=None):
    """Create bar chart for state comparison"""
    if df.empty or 'state' not in df.columns:
        return go.Figure()
    
    # Filter to selected states
    df = df[df['state'].isin(selected_states)]
    
    # Identify metric column if not provided
    if not metric_column:
        # Try to use enrollment or premium as default
        enrollment_col = next((col for col in df.columns if 'enrollment' in col.lower()), None)
        premium_col = next((col for col in df.columns if 'premium' in col.lower()), None)
        metric_column = enrollment_col or premium_col
    
    if not metric_column or metric_column not in df.columns:
        return go.Figure()
    
    # Convert metric column to numeric
    try:
        df[metric_column] = pd.to_numeric(df[metric_column], errors='coerce')
    except:
        pass
    
    # Create comparison chart
    fig = px.bar(
        df,
        x='state',
        y=metric_column,
        title=f"State Comparison: {metric_column.replace('_', ' ').title()}",
        text=metric_column
    )
    
    fig.update_layout(
        xaxis_title="State",
        yaxis_title=metric_column.replace('_', ' ').title()
    )
    
    # Format text labels
    fig.update_traces(texttemplate='%{text:,}', textposition='outside')
    
    return fig

def create_enrollment_growth_chart(growth_df, year_column, growth_column):
    """Create bar chart for enrollment growth rates"""
    if growth_df.empty or year_column not in growth_df.columns or growth_column not in growth_df.columns:
        return go.Figure()
    
    # Convert growth column to numeric
    try:
        growth_df[growth_column] = pd.to_numeric(growth_df[growth_column], errors='coerce')
    except:
        pass
    
    fig = px.bar(
        growth_df,
        x=year_column,
        y=growth_column,
        title="Year-over-Year Enrollment Growth",
        text=growth_column
    )
    
    fig.update_layout(
        xaxis_title="Year",
        yaxis_title="Growth Rate (%)"
    )
    
    # Format text labels
    fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
    
    # Color bars based on positive/negative values
    fig.update_traces(marker_color=np.where(growth_df[growth_column] >= 0, 'green', 'red'))
    
    return fig

def create_county_map(county_df, state, value_column, title):
    """Create county-level choropleth map for a specific state"""
    if county_df.empty or 'state' not in county_df.columns or value_column not in county_df.columns:
        return go.Figure()
    
    # Filter to specified state
    state_df = county_df[county_df['state'] == state]
    
    # Check if we have FIPS codes
    fips_col = next((col for col in state_df.columns if 'fips' in col.lower()), None)
    county_col = next((col for col in state_df.columns if 'county' in col.lower()), None)
    
    if not fips_col or not county_col or state_df.empty:
        return go.Figure()
    
    # Convert value column to numeric
    try:
        state_df[value_column] = pd.to_numeric(state_df[value_column], errors='coerce')
    except:
        pass
    
    fig = px.choropleth(
        state_df,
        geojson="https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json",
        locations=fips_col,
        color=value_column,
        scope="usa",
        color_continuous_scale="Blues",
        title=title,
        hover_name=county_col,
        hover_data={fips_col: False, value_column: True}
    )
    
    # Zoom to state
    fig.update_layout(geo=dict(scope='usa'))
    
    return fig 