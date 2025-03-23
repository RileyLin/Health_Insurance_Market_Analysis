# Health Insurance Market Analysis Dashboard

A comprehensive data visualization and analysis tool for exploring health insurance marketplace data from the Centers for Medicare & Medicaid Services (CMS) Open Enrollment Period (OEP) Public Use Files.

## Overview

This interactive dashboard analyzes health insurance marketplace data to provide insights into enrollment patterns, premium trends, demographic breakdowns, geographic distributions, and plan selection behaviors across the United States.

## Features

- **Overview Dashboard**: Key performance indicators, nationwide enrollment map, top states by enrollment, metal level distribution, and enrollment trends
- **Premium Analysis**: State-specific premium insights, premium trends over time, premiums by metal level, and subsidy breakdowns
- **Demographic Insights**: Age distribution, gender breakdown, income level distribution, race/ethnicity enrollment patterns, and rural/urban analysis
- **Geographic Analysis**: State-to-state comparison tool, county-level analysis, and customizable nationwide maps
- **Plan Selection Patterns**: Metal level popularity trends, new vs. returning consumer behavior, HSA-eligible plan selection, and deductible trends

## Data Sources

The dashboard utilizes data from the following CMS Public Use Files:
- 2024 OEP State-Level Public Use File
- 2024 OEP County-Level Public Use File
- 2014-2024 OEP Plan Design Public Use File

## Project Structure

```
project_root/
├── app.py                  # Main Streamlit application
├── data/                   # Raw data files
├── src/
│   ├── data_loader.py      # Data loading and processing
│   ├── metrics.py          # Key metric calculations
│   ├── visualizations.py   # Visualization components
│   └── utils.py            # Helper functions
└── README.md               # Project documentation
```

## Installation

1. Clone the repository:
```
git clone https://github.com/yourusername/health-insurance-market-analysis.git
cd health-insurance-market-analysis
```

2. Install the required dependencies:
```
pip install -r requirements.txt
```

3. Place the data files in the `data/` directory:
   - `2024 OEP State-Level Public Use File.csv` or `.xlsx`
   - `2024 OEP County-Level Public Use File.csv` or `.xlsx`
   - `2014-2024 OEP Plan Design Public Use File.csv` or `.xlsx`

## Usage

Run the Streamlit application:
```
streamlit run app.py
```

Navigate to `http://localhost:8501` in your web browser to access the dashboard.

## Requirements

- Python 3.8+
- Pandas
- NumPy
- Streamlit
- Plotly
- Openpyxl (for Excel file support)

## Advanced Features

- **Data Transformation Pipeline**: Automatic conversion from Excel to CSV for faster loading
- **Dynamic Column Detection**: Intelligent identification of relevant columns across different datasets
- **Metric Engineering**: Calculated fields such as affordability ratios and market penetration
- **Performance Optimization**: Data caching for improved dashboard responsiveness

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Credits

Data provided by the Centers for Medicare & Medicaid Services (CMS) Open Enrollment Period (OEP) Public Use Files.

## Contact

For questions or feedback, please open an issue on GitHub or contact [your_email@example.com]. 