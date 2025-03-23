import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import time
from src.data_loader import load_state_data, load_county_data, load_historical_data, convert_excel_to_csv
from src.visualizations import (
    create_map, create_premium_chart, create_demographic_chart, create_metal_level_chart,
    create_state_comparison_chart, create_enrollment_growth_chart, create_county_map
)
from src.metrics import (
    calculate_kpis, calculate_enrollment_growth, calculate_market_penetration,
    calculate_premium_affordability, calculate_plan_value_metric
)
from src.utils import (
    get_state_mapping, get_metal_level_colors, format_currency, format_percentage,
    format_number, get_trend_emoji, calculate_growth, get_top_n_states
)

# Set page configuration
st.set_page_config(
    page_title="Health Insurance Market Analysis",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #424242;
    }
    .kpi-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
    }
    .kpi-value {
        font-size: 2rem;
        font-weight: bold;
    }
    .kpi-title {
        font-size: 1rem;
        color: #616161;
    }
    .trend-up {
        color: #4CAF50;
    }
    .trend-down {
        color: #F44336;
    }
    .footer {
        margin-top: 3rem;
        text-align: center;
        color: #9e9e9e;
        font-size: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar navigation
st.sidebar.title("Health Insurance Market Analysis")
st.sidebar.image("https://www.cms.gov/sites/default/files/styles/media_crop_16_9/public/2020-02/marketplace-logo.png", width=200)

page = st.sidebar.selectbox(
    "Select Dashboard View",
    ["Overview", "Premium Analysis", "Demographic Insights", "Geographic Analysis", "Plan Selection Patterns"]
)

# Add information about the data
st.sidebar.markdown("---")
st.sidebar.subheader("About the Data")
st.sidebar.markdown("""
This dashboard analyzes data from the CMS Open Enrollment Period (OEP) Public Use Files:
- State-level data (2024)
- County-level data (2024)
- Historical plan design data (2014-2024)
""")

# Add filters in sidebar
st.sidebar.markdown("---")
st.sidebar.subheader("Global Filters")

# Data loading with caching
@st.cache_data(ttl=3600)
def load_all_data():
    # Convert Excel files to CSV for faster loading if needed
    convert_excel_to_csv()
    
    # Load data
    state_df = load_state_data()
    county_df = load_county_data()
    historical_df = load_historical_data()
    
    # Add state codes if missing
    if state_df is not None and not state_df.empty and 'state' in state_df.columns:
        state_mapping = get_state_mapping()
        if 'state_code' not in state_df.columns:
            state_df['state_code'] = state_df['state'].map(state_mapping)
    
    return state_df, county_df, historical_df

# Show loading spinner while data loads
with st.spinner("Loading data... This may take a moment"):
    state_df, county_df, historical_df = load_all_data()

# Add debug info
st.sidebar.markdown("---")
st.sidebar.subheader("Debug Info")
if not state_df.empty:
    st.sidebar.write(f"State data loaded: {len(state_df)} rows")
    if 'total_enrollments' in state_df.columns:
        st.sidebar.write(f"Total enrollments sum: {state_df['total_enrollments'].sum()}")
        st.sidebar.write(f"Total enrollments range: {state_df['total_enrollments'].min()} to {state_df['total_enrollments'].max()}")
    else:
        st.sidebar.write("No 'total_enrollments' column found")
        st.sidebar.write(f"Available columns: {state_df.columns.tolist()[:5]}...")
else:
    st.sidebar.write("State data is empty")
    
if not county_df.empty:
    st.sidebar.write(f"County data loaded: {len(county_df)} rows")
else:
    st.sidebar.write("County data is empty")

# Check if data loading was successful
if state_df.empty:
    st.error("Error loading state-level data. Please check that the data files exist and are correctly formatted.")
    st.stop()

# Add year filter if we have historical data
available_years = []
if not historical_df.empty:
    year_col = next((col for col in historical_df.columns if 'year' in col.lower()), None)
    if year_col:
        available_years = sorted(historical_df[year_col].unique())
        
        selected_years = st.sidebar.slider(
            "Select Year Range",
            min_value=int(min(available_years)),
            max_value=int(max(available_years)),
            value=(int(min(available_years)), int(max(available_years)))
        )

# Overview Page
if page == "Overview":
    st.markdown("<h1 class='main-header'>Health Insurance Marketplace Overview</h1>", unsafe_allow_html=True)
    
    # Display KPIs and summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_enrollments = calculate_kpis(state_df, 'total_enrollments')
        st.markdown(f"""
        <div class='kpi-card'>
            <div class='kpi-value'>{format_number(total_enrollments)}</div>
            <div class='kpi-title'>Total Enrollments</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        avg_premium = calculate_kpis(state_df, 'avg_premium')
        st.markdown(f"""
        <div class='kpi-card'>
            <div class='kpi-value'>{format_currency(avg_premium)}</div>
            <div class='kpi-title'>Average Monthly Premium</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        pct_with_aptc = calculate_kpis(state_df, 'pct_with_aptc')
        st.markdown(f"""
        <div class='kpi-card'>
            <div class='kpi-value'>{format_percentage(pct_with_aptc)}</div>
            <div class='kpi-title'>With Financial Assistance</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        # Calculate number of participating states
        num_states = len(state_df['state'].unique())
        st.markdown(f"""
        <div class='kpi-card'>
            <div class='kpi-value'>{num_states}</div>
            <div class='kpi-title'>Participating States</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Nationwide enrollment map
    st.markdown("<h2 class='sub-header'>Nationwide Enrollment Map</h2>", unsafe_allow_html=True)
    enrollment_map = create_map(
        state_df,
        'total_enrollments',
        'Total Marketplace Enrollments by State (2024)'
    )
    st.plotly_chart(enrollment_map, use_container_width=True)
    
    # Top 10 states by enrollment
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("<h2 class='sub-header'>Top 10 States by Enrollment</h2>", unsafe_allow_html=True)
        top_states = get_top_n_states(state_df, 'total_enrollments', n=10)
        fig = create_state_comparison_chart(top_states, top_states['state'].tolist(), 'total_enrollments')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("<h2 class='sub-header'>Metal Level Distribution</h2>", unsafe_allow_html=True)
        
        # Check if we have metal level data in state_df or historical_df
        metal_col_state = next((col for col in state_df.columns if 'metal' in col.lower()), None)
        metal_col_hist = next((col for col in historical_df.columns if 'metal' in col.lower()), None)
        
        if metal_col_state:
            fig = create_metal_level_chart(state_df, metal_col_state)
        elif metal_col_hist and not historical_df.empty:
            # Use the most recent year from historical data
            year_col = next((col for col in historical_df.columns if 'year' in col.lower()), None)
            if year_col:
                max_year = historical_df[year_col].max()
                recent_data = historical_df[historical_df[year_col] == max_year]
                fig = create_metal_level_chart(recent_data, metal_col_hist, year_col)
            else:
                fig = create_metal_level_chart(historical_df, metal_col_hist)
        else:
            st.warning("Metal level data not available")
            fig = None
            
        if fig:
            st.plotly_chart(fig, use_container_width=True)

    # Year-over-year enrollment changes if we have historical data
    st.markdown("---")
    st.markdown("<h2 class='sub-header'>Enrollment Trends</h2>", unsafe_allow_html=True)
    
    if not historical_df.empty:
        year_col = next((col for col in historical_df.columns if 'year' in col.lower()), None)
        enrollment_col = next((col for col in historical_df.columns if 'enrollment' in col.lower()), None)
        
        if year_col and enrollment_col:
            # Group by year and calculate totals
            yearly_data = historical_df.groupby(year_col)[enrollment_col].sum().reset_index()
            yearly_data['growth'] = yearly_data[enrollment_col].pct_change() * 100
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig = create_enrollment_growth_chart(yearly_data, year_col, 'growth')
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Create line chart of total enrollments
                fig = create_premium_chart(yearly_data, None, year_col, enrollment_col)
                fig.update_layout(title="Total Enrollments by Year", yaxis_title="Total Enrollments")
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Historical enrollment data not available")

# Premium Analysis Page
elif page == "Premium Analysis":
    st.markdown("<h1 class='main-header'>Premium Analysis</h1>", unsafe_allow_html=True)
    
    # State selector for detailed analysis
    states = sorted(state_df['state'].unique())
    selected_state = st.selectbox("Select a state for detailed analysis", states)
    
    # Filter data for selected state
    state_data = state_df[state_df['state'] == selected_state]
    
    # Display state-specific KPIs
    col1, col2, col3 = st.columns(3)
    
    with col1:
        avg_premium = state_data['average_premium'].values[0] if 'average_premium' in state_data.columns else 0
        st.markdown(f"""
        <div class='kpi-card'>
            <div class='kpi-value'>{format_currency(avg_premium)}</div>
            <div class='kpi-title'>Average Premium in {selected_state}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        # Calculate premium after APTC if we have the data
        if 'average_premium_after_aptc' in state_data.columns:
            avg_premium_after_aptc = state_data['average_premium_after_aptc'].values[0]
            st.markdown(f"""
            <div class='kpi-card'>
                <div class='kpi-value'>{format_currency(avg_premium_after_aptc)}</div>
                <div class='kpi-title'>Avg. Premium After APTC</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class='kpi-card'>
                <div class='kpi-value'>N/A</div>
                <div class='kpi-title'>Avg. Premium After APTC</div>
            </div>
            """, unsafe_allow_html=True)
    
    with col3:
        # Calculate average savings from APTC
        if 'average_premium' in state_data.columns and 'average_premium_after_aptc' in state_data.columns:
            avg_savings = state_data['average_premium'].values[0] - state_data['average_premium_after_aptc'].values[0]
            st.markdown(f"""
            <div class='kpi-card'>
                <div class='kpi-value'>{format_currency(avg_savings)}</div>
                <div class='kpi-title'>Average APTC Savings</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class='kpi-card'>
                <div class='kpi-value'>N/A</div>
                <div class='kpi-title'>Average APTC Savings</div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Premium trends by state (if we have historical data)
    if not historical_df.empty:
        st.markdown("<h2 class='sub-header'>Premium Trends Over Time</h2>", unsafe_allow_html=True)
        
        # Identify relevant columns
        year_col = next((col for col in historical_df.columns if 'year' in col.lower()), None)
        state_col = next((col for col in historical_df.columns if col.lower() == 'state'), None)
        premium_col = next((col for col in historical_df.columns if 'premium' in col.lower()), None)
        
        if year_col and state_col and premium_col:
            # Filter historical data for the selected state
            state_historical = historical_df[historical_df[state_col] == selected_state]
            
            if not state_historical.empty:
                # Group by year and calculate average premiums
                yearly_premiums = state_historical.groupby(year_col)[premium_col].mean().reset_index()
                
                # Create premium trend chart
                fig = create_premium_chart(yearly_premiums, None, year_col, premium_col)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info(f"Historical premium data not available for {selected_state}")
        else:
            st.info("Historical premium data not available")
    
    # Premium comparison by metal level
    st.markdown("<h2 class='sub-header'>Premium by Metal Level</h2>", unsafe_allow_html=True)
    
    # Check if we have metal level data
    metal_col = next((col for col in state_df.columns if 'metal' in col.lower()), None)
    premium_col = next((col for col in state_df.columns if 'premium' in col.lower()), None)
    
    if metal_col and premium_col:
        # Group by metal level and calculate average premiums
        metal_premiums = state_df.groupby(metal_col)[premium_col].mean().reset_index()
        
        # Create bar chart
        fig = px.bar(
            metal_premiums,
            x=metal_col,
            y=premium_col,
            color=metal_col,
            color_discrete_map=get_metal_level_colors(),
            title="Average Premium by Metal Level",
            labels={premium_col: "Average Premium ($)", metal_col: "Metal Level"}
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Metal level premium data not available")
    
    # Premium vs. subsidy breakdown
    st.markdown("<h2 class='sub-header'>Premium vs. Subsidy Breakdown</h2>", unsafe_allow_html=True)
    
    if 'average_premium' in state_df.columns and 'average_aptc' in state_df.columns:
        # Create state comparison with premiums and subsidies
        state_comparison = state_df.copy()
        state_comparison['net_premium'] = state_comparison['average_premium'] - state_comparison['average_aptc']
        
        # Create stacked bar chart
        fig = px.bar(
            state_comparison,
            x='state',
            y=['average_aptc', 'net_premium'],
            title="Premium and Subsidy Breakdown by State",
            labels={'value': 'Amount ($)', 'variable': 'Component'},
            color_discrete_map={
                'average_aptc': '#4CAF50',  # Green for subsidy
                'net_premium': '#1E88E5'    # Blue for net premium
            }
        )
        
        fig.update_layout(
            xaxis_title="State",
            yaxis_title="Amount ($)",
            legend_title="Component",
            hovermode="x unified"
        )
        
        # Highlight selected state
        selected_state_index = state_comparison[state_comparison['state'] == selected_state].index[0]
        highlight_colors = ['#1E88E5'] * len(state_comparison)
        highlight_colors[selected_state_index] = '#FFC107'  # Yellow highlight
        
        # Show the chart
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Premium and subsidy breakdown data not available")

# Demographic Insights Page
elif page == "Demographic Insights":
    st.markdown("<h1 class='main-header'>Demographic Insights</h1>", unsafe_allow_html=True)
    
    # Age distribution
    st.markdown("<h2 class='sub-header'>Age Distribution of Enrollees</h2>", unsafe_allow_html=True)
    
    # Create age distribution chart using our special age handler
    fig = create_demographic_chart(state_df, 'age', "Enrollment by Age Group")
    st.plotly_chart(fig, use_container_width=True)
    
    # Gender breakdown and Income level in two columns
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("<h2 class='sub-header'>Gender Breakdown</h2>", unsafe_allow_html=True)
        
        # Create gender breakdown chart using our special gender handler
        fig = create_demographic_chart(state_df, 'gender', "Enrollment by Gender")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("<h2 class='sub-header'>Income Level Distribution</h2>", unsafe_allow_html=True)
        
        # Create income distribution chart using our special income handler
        fig = create_demographic_chart(state_df, 'income', "Enrollment by Income Level")
        st.plotly_chart(fig, use_container_width=True)
    
    # Race/ethnicity breakdown
    st.markdown("<h2 class='sub-header'>Race/Ethnicity Enrollment Patterns</h2>", unsafe_allow_html=True)
    
    # Check if we have race/ethnicity columns
    race_cols = [col for col in state_df.columns if any(r in col.lower() for r in ['race', 'ethnicity', 'hspnc', 'aian', 'asn', 'nhpi', 'black', 'wht'])]
    
    if race_cols:
        st.info("Race/ethnicity data is available but needs special processing. We'll implement this in a future update.")
    else:
        st.info("Race/ethnicity data not available in this dataset")
    
    # Rural vs. urban enrollment
    st.markdown("<h2 class='sub-header'>Rural vs. Urban Enrollment</h2>", unsafe_allow_html=True)
    
    # Check for rural/urban columns
    rural_cols = [col for col in state_df.columns if 'rural' in col.lower() or 'rrl' in col.lower()]
    
    if rural_cols:
        # Create a special rural/urban dataframe
        rural_data = []
        
        # Check for specific rural/urban columns
        if 'rural' in state_df.columns and 'non_rural' in state_df.columns:
            rural_total = state_df['rural'].sum()
            non_rural_total = state_df['non_rural'].sum()
            
            if rural_total > 0:
                rural_data.append({'location_type': 'Rural', 'enrollment': rural_total})
            if non_rural_total > 0:
                rural_data.append({'location_type': 'Urban', 'enrollment': non_rural_total})
        
        # Alternative column names
        elif 'rrl' in state_df.columns and 'non_rrl' in state_df.columns:
            rural_total = state_df['rrl'].sum()
            non_rural_total = state_df['non_rrl'].sum()
            
            if rural_total > 0:
                rural_data.append({'location_type': 'Rural', 'enrollment': rural_total})
            if non_rural_total > 0:
                rural_data.append({'location_type': 'Urban', 'enrollment': non_rural_total})
        
        if rural_data:
            # Create rural/urban pie chart
            rural_df = pd.DataFrame(rural_data)
            fig = px.pie(
                rural_df,
                values='enrollment',
                names='location_type',
                title="Rural vs. Urban Enrollment",
                hole=0.4,
                color='location_type',
                color_discrete_map={
                    'Rural': '#4CAF50',
                    'Urban': '#1E88E5'
                }
            )
            
            # Improve formatting
            fig.update_traces(textposition='inside', textinfo='percent+label')
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Rural vs. urban enrollment data not available")
    else:
        st.info("Rural vs. urban enrollment data not available")

# Geographic Analysis Page
elif page == "Geographic Analysis":
    st.title("Geographic Analysis")
    
    # Verify we have the necessary dataframes
    has_state_data = 'state_df' in locals() and not state_df.empty
    has_county_data = 'county_df' in locals() and not county_df.empty
    
    if not has_state_data and not has_county_data:
        st.error("No geographic data available. Please check the data loading process.")
        st.stop()
    
    # State Comparison Tool
    st.header("State Comparison Tool")
    
    if has_state_data:
        # Identify state column (could be 'State_Abrvtn' in our dataset)
        state_code_col = next((col for col in state_df.columns if 'state' in col.lower() or 'abrvtn' in col.lower()), None)
        
        if state_code_col:
            st.sidebar.subheader("State Comparison Settings")
            
            # Get available states from the data
            available_states = sorted(state_df[state_code_col].unique().tolist())
            
            # Select default states (choose a few popular ones if available)
            default_states = []
            for state in ['CA', 'TX', 'NY', 'FL']:
                if state in available_states:
                    default_states.append(state)
            
            # If no defaults were found or less than 2, use the first few states
            if len(default_states) < 2:
                default_states = available_states[:min(4, len(available_states))]
            
            # Allow user to select states for comparison
            selected_states = st.sidebar.multiselect(
                "Select states to compare:",
                options=available_states,
                default=default_states
            )
            
            # Ensure at least one state is selected
            if not selected_states:
                st.warning("Please select at least one state for comparison.")
                selected_states = [default_states[0]] if default_states else [available_states[0]]
            
            # Get numeric columns for metrics
            numeric_cols = [col for col in state_df.columns if 
                            state_df[col].dtype in ['int64', 'float64'] and 
                            col != state_code_col and
                            'fips' not in col.lower()]
            
            if numeric_cols:
                # Let user select metric for comparison
                selected_metric = st.sidebar.selectbox(
                    "Select metric for comparison:",
                    options=numeric_cols,
                    index=0
                )
                
                # Filter dataframe for selected states
                filtered_df = state_df[state_df[state_code_col].isin(selected_states)].copy()
                
                if not filtered_df.empty:
                    # Create comparison chart
                    fig = px.bar(
                        filtered_df,
                        x=state_code_col,
                        y=selected_metric,
                        title=f"{selected_metric} by State",
                        color=state_code_col,
                        labels={selected_metric: selected_metric.replace('_', ' ').title()}
                    )
                    st.plotly_chart(fig)
                    
                    # Show the data in a table
                    st.subheader("Data Table")
                    st.dataframe(filtered_df[[state_code_col, selected_metric]])
                else:
                    st.warning(f"No data available for the selected states: {', '.join(selected_states)}")
            else:
                st.error("No numeric columns available for comparison.")
        else:
            st.error("No state column found in the data.")
    else:
        st.warning("State-level data is not available for comparison.")
    
    # County-Level Analysis
    if has_county_data:
        st.header("County-Level Analysis")
        
        # Identify state and county columns
        state_col = next((col for col in county_df.columns if 'state' in col.lower() or 'abrvtn' in col.lower()), None)
        county_col = next((col for col in county_df.columns if 'county' in col.lower() or 'fips' in col.lower()), None)
        
        if state_col and county_col:
            st.sidebar.subheader("County Analysis Settings")
            
            # Get available states from county data
            states_with_counties = sorted(county_df[state_col].unique().tolist())
            
            # Select state for county analysis
            selected_state = st.sidebar.selectbox(
                "Select state for county analysis:",
                options=states_with_counties
            )
            
            # Filter for the selected state
            state_counties = county_df[county_df[state_col] == selected_state].copy()
            
            if not state_counties.empty:
                # Get numeric columns for county metrics
                county_metrics = [col for col in state_counties.columns if 
                                 state_counties[col].dtype in ['int64', 'float64'] and 
                                 col != county_col and 'fips' not in col.lower()]
                
                if county_metrics:
                    # Let user select metric for county analysis
                    county_metric = st.sidebar.selectbox(
                        "Select metric for county analysis:",
                        options=county_metrics
                    )
                    
                    # Create county comparison chart
                    fig = px.bar(
                        state_counties.sort_values(county_metric, ascending=False),
                        x=county_col,
                        y=county_metric,
                        title=f"{county_metric} by County in {selected_state}",
                        labels={county_metric: county_metric.replace('_', ' ').title()}
                    )
                    st.plotly_chart(fig)
                    
                    # Show top and bottom counties
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader(f"Top 5 Counties by {county_metric}")
                        top_counties = state_counties.sort_values(county_metric, ascending=False).head(5)
                        st.dataframe(top_counties[[county_col, county_metric]])
                    
                    with col2:
                        st.subheader(f"Bottom 5 Counties by {county_metric}")
                        bottom_counties = state_counties.sort_values(county_metric).head(5)
                        st.dataframe(bottom_counties[[county_col, county_metric]])
                else:
                    st.error("No numeric columns available for county analysis.")
            else:
                st.warning(f"No county data available for {selected_state}.")
        else:
            st.error("State or county columns not found in county data.")
    else:
        st.warning("County-level data is not available for analysis.")
    
    # National Enrollment Map
    st.header("Nationwide Enrollment Map")
    
    if has_state_data:
        # Prepare data for map
        # First, check if we have enrollment or consumer data
        enrollment_col = next((col for col in state_df.columns if 'enrollment' in col.lower() or 'consumer' in col.lower() or 'cnsmr' in col.lower()), None)
        state_code_col = next((col for col in state_df.columns if 'state' in col.lower() or 'abrvtn' in col.lower()), None)
        
        if enrollment_col and state_code_col:
            # Create nationwide enrollment map
            map_title = f"{enrollment_col.replace('_', ' ').title()} by State"
            enrollment_map = create_map(state_df, enrollment_col, map_title)
            st.plotly_chart(enrollment_map)
        else:
            st.warning("Enrollment or state code data not found for creating nationwide map.")
    else:
        st.warning("State-level data not available for nationwide map.")

# Plan Selection Patterns Page
elif page == "Plan Selection Patterns":
    st.markdown("<h1 class='main-header'>Plan Selection Patterns</h1>", unsafe_allow_html=True)
    
    # Metal level popularity
    st.markdown("<h2 class='sub-header'>Metal Level Popularity</h2>", unsafe_allow_html=True)
    
    # Check for metal level columns
    metal_cols = {
        'bronze': 'Bronze',
        'silver': 'Silver',
        'gold': 'Gold',
        'platinum': 'Platinum',
        'catastrophic': 'Catastrophic'
    }
    
    found_metal_cols = [col for col in metal_cols.keys() if col in state_df.columns]
    
    if found_metal_cols:
        # Create a DataFrame for metal level data
        metal_data = []
        for col, label in metal_cols.items():
            if col in state_df.columns:
                total = state_df[col].sum()
                if total > 0:
                    metal_data.append({
                        'metal_level': label,
                        'enrollment': total
                    })
        
        if metal_data:
            metal_df = pd.DataFrame(metal_data)
            
            # Create donut chart
            fig = px.pie(
                metal_df,
                values='enrollment',
                names='metal_level',
                title="Enrollment by Metal Level",
                hole=0.4,
                color='metal_level',
                color_discrete_map={
                    'Bronze': '#CD7F32',
                    'Silver': '#C0C0C0',
                    'Gold': '#FFD700',
                    'Platinum': '#7E909A',
                    'Catastrophic': '#E57373'
                }
            )
            
            # Improve formatting
            fig.update_traces(textposition='inside', textinfo='percent+label')
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Metal level data not available")
    else:
        st.info("Metal level data not available")
    
    # New vs. returning consumer behavior
    st.markdown("<h2 class='sub-header'>New vs. Returning Consumer Behavior</h2>", unsafe_allow_html=True)
    
    # Use our special consumer type chart
    fig = create_demographic_chart(state_df, 'consumer_type', "New vs. Returning Consumers")
    st.plotly_chart(fig, use_container_width=True)
    
    # Premium by metal level if we have the data
    if found_metal_cols and 'average_premium' in state_df.columns:
        st.markdown("<h2 class='sub-header'>Average Premium by Metal Level</h2>", unsafe_allow_html=True)
        
        # Create a DataFrame with premium by metal level data
        premium_data = []
        
        # Group by states first
        for state_code in state_df['state_code'].unique():
            state_data = state_df[state_df['state_code'] == state_code]
            
            # For each metal level with premium data
            if 'average_premium' in state_data.columns:
                for col, label in metal_cols.items():
                    if col in state_data.columns and state_data[col].iloc[0] > 0:
                        premium_data.append({
                            'state': state_data['state'].iloc[0],
                            'metal_level': label,
                            'average_premium': state_data['average_premium'].iloc[0]
                        })
        
        if premium_data:
            premium_df = pd.DataFrame(premium_data)
            
            # Group by metal level and calculate average premium
            metal_premium = premium_df.groupby('metal_level')['average_premium'].mean().reset_index()
            
            # Sort by expected metal level order
            metal_order = ['Catastrophic', 'Bronze', 'Silver', 'Gold', 'Platinum']
            metal_premium['sort_order'] = metal_premium['metal_level'].map({level: i for i, level in enumerate(metal_order)})
            metal_premium = metal_premium.sort_values('sort_order')
            
            # Create bar chart
            fig = px.bar(
                metal_premium,
                x='metal_level',
                y='average_premium',
                color='metal_level',
                title="Average Premium by Metal Level",
                labels={'metal_level': 'Metal Level', 'average_premium': 'Average Premium ($)'},
                color_discrete_map={
                    'Bronze': '#CD7F32',
                    'Silver': '#C0C0C0',
                    'Gold': '#FFD700',
                    'Platinum': '#7E909A',
                    'Catastrophic': '#E57373'
                }
            )
            
            # Format y-axis as currency
            fig.update_layout(
                yaxis=dict(
                    tickprefix="$",
                    separatethousands=True
                )
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Premium by metal level data not available")
    else:
        st.info("Premium by metal level data not available")
        
    # HSA-eligible plan selection if we have the data
    if 'hsa' in ' '.join(state_df.columns).lower():
        st.markdown("<h2 class='sub-header'>HSA-Eligible Plan Selection</h2>", unsafe_allow_html=True)
        
        # Find HSA column
        hsa_col = next((col for col in state_df.columns if 'hsa' in col.lower()), None)
        
        if hsa_col:
            fig = create_demographic_chart(state_df, hsa_col, "HSA-Eligible Plan Selection")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("HSA-eligible plan data not available")
    else:
        st.info("HSA-eligible plan data not available")

# Footer
st.markdown("---")
st.markdown("""
<div class='footer'>
    <p>Data Source: CMS Open Enrollment Period (OEP) Public Use Files</p>
    <p>© 2024 Health Insurance Market Analysis Dashboard</p>
</div>
""", unsafe_allow_html=True) 