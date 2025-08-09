# Chemical Process Monitoring Dashboard

## Overview

This repository contains a Dash-based chemical process monitoring dashboard that provides real-time visualization, historical analysis, alert management, and data export capabilities for industrial chemical processes. The application is designed to monitor critical parameters like temperature, pressure, pH, flow rate, and concentration, with comprehensive alerting and reporting features. Recently migrated from Streamlit to Dash for better performance and interactivity.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Framework**: Dash web application with Bootstrap styling
- **Layout**: Tab-based navigation with responsive design
- **Navigation**: Top-level tabs for different sections
- **UI Components**: Interactive charts using Plotly, data tables, forms, and Bootstrap cards
- **State Management**: Dash callbacks for real-time interactivity

### Backend Architecture
- **Data Storage**: JSON file-based storage system for simplicity and portability
- **Modular Design**: Utility classes organized in separate modules
- **Processing**: Real-time data processing and statistical analysis
- **Alert System**: Rule-based threshold monitoring with configurable parameters

### File Structure
```
app.py                      # Main dashboard application
pages/
├── 1_Data_Input.py        # Data input and file upload
├── 2_Historical_Analysis.py # Historical data analysis
├── 3_Alerts_Config.py     # Alert configuration
└── 4_Data_Export.py       # Data export and reporting
utils/
├── data_manager.py        # Data storage and retrieval
├── alert_system.py        # Alert management
├── statistics.py          # Statistical calculations
└── visualization.py       # Chart generation
```

## Key Components

### 1. Data Management (`utils/data_manager.py`)
- **Purpose**: Handles all data storage and retrieval operations
- **Storage Format**: JSON files for easy backup and portability
- **Features**: Data validation, CRUD operations, metadata tracking
- **File Location**: `data/process_data.json`

### 2. Alert System (`utils/alert_system.py`)
- **Purpose**: Manages alert configurations and threshold monitoring
- **Features**: Configurable thresholds, alert history, cooldown management
- **Storage**: Separate JSON files for configuration and history
- **Alert Types**: Upper/lower bounds, rate of change detection

### 3. Visualization Engine (`utils/visualization.py`)
- **Purpose**: Generates interactive charts and graphs
- **Library**: Plotly for interactive visualizations
- **Chart Types**: Line charts, scatter plots, histograms, correlation matrices
- **Features**: Customizable styling, hover interactions, responsive design

### 4. Statistics Calculator (`utils/statistics.py`)
- **Purpose**: Provides statistical analysis capabilities
- **Features**: Basic statistics, correlation analysis, trend detection
- **Libraries**: Pandas, NumPy, SciPy for mathematical operations

### 5. Multi-Page Application Structure
- **Main Dashboard**: Real-time monitoring and current status
- **Data Input**: File upload, manual entry, and data simulation
- **Historical Analysis**: Trend analysis and pattern recognition
- **Alerts Configuration**: Threshold management and alert monitoring
- **Data Export**: Report generation and data export functionality

## Data Flow

1. **Data Input**:
   - CSV file uploads processed and validated
   - Manual data entry through forms
   - Simulated data generation for testing
   - Data stored in JSON format with metadata

2. **Processing Pipeline**:
   - Real-time data validation and cleaning
   - Statistical calculations performed on-demand
   - Alert threshold checking for each data point
   - Historical data aggregation for analysis

3. **Visualization**:
   - Data retrieved from storage
   - Charts generated using Plotly
   - Interactive filtering and date range selection
   - Real-time updates for current metrics

4. **Alert Management**:
   - Continuous monitoring of configured thresholds
   - Alert generation and history tracking
   - Cooldown periods to prevent spam
   - Configurable notification preferences

## External Dependencies

### Core Libraries
- **dash**: Web application framework
- **dash-bootstrap-components**: Bootstrap components for Dash
- **pandas**: Data manipulation and analysis
- **numpy**: Numerical computing
- **plotly**: Interactive visualization library
- **scipy**: Scientific computing for statistics

### Data Storage
- **JSON files**: Local file-based storage system
- **No database required**: Simplified deployment and maintenance

### File Dependencies
- Configuration files stored in `data/` directory
- Process data in `data/process_data.json`
- Alert configuration in `data/alert_config.json`
- Alert history in `data/alert_history.json`

## Deployment Strategy

### Local Development
- **Requirements**: Python 3.7+ with required packages
- **Command**: `python app.py`
- **Port**: Port 5000 for Replit compatibility

### Production Considerations
- **Scalability**: File-based storage suitable for small to medium datasets
- **Backup**: JSON files can be easily backed up and version controlled
- **Security**: No authentication implemented (suitable for internal networks)
- **Performance**: Caching implemented for data loading and processing

### Configuration Management
- **Environment Variables**: None currently used
- **Configuration Files**: JSON-based configuration for flexibility
- **Data Directory**: Automatically created if not exists
- **Default Settings**: Sensible defaults for immediate use

### Future Enhancements
The architecture supports easy migration to:
- Database backend (PostgreSQL, MongoDB)
- User authentication and authorization
- Real-time data streaming
- Advanced ML-based anomaly detection
- Email/SMS notification systems