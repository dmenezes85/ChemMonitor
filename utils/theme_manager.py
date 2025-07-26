import streamlit as st

def apply_theme_css():
    """Apply theme-based CSS styling to the Streamlit app."""
    theme_mode = st.session_state.get('theme_mode', 'Claro')
    
    if theme_mode == "Escuro":
        st.markdown("""
        <style>
        .stApp {
            background-color: #0E1117 !important;
            color: #FAFAFA !important;
        }
        .stSidebar {
            background-color: #262730 !important;
        }
        .stSidebar .stSelectbox > div > div,
        .stSidebar .stMultiSelect > div > div,
        .stSidebar .stTextInput > div > div > input,
        .stSidebar .stNumberInput > div > div > input,
        .stSidebar .stDateInput > div > div > input,
        .stSidebar .stTimeInput > div > div > input {
            background-color: #262730 !important;
            color: #FAFAFA !important;
            border-color: #404040 !important;
        }
        .stMetric {
            background-color: #262730 !important;
            padding: 1rem !important;
            border-radius: 0.5rem !important;
            border: 1px solid #404040 !important;
        }
        .stDataFrame, .stTable {
            background-color: #262730 !important;
            color: #FAFAFA !important;
        }
        .stTabs [data-baseweb="tab-list"] {
            background-color: #262730 !important;
        }
        .stTabs [data-baseweb="tab"] {
            background-color: #262730 !important;
            color: #FAFAFA !important;
        }
        .stTabs [aria-selected="true"] {
            background-color: #FF6B6B !important;
            color: #FAFAFA !important;
        }
        .stMarkdown {
            color: #FAFAFA !important;
        }
        .stAlert {
            background-color: #262730 !important;
            color: #FAFAFA !important;
        }
        .stForm {
            background-color: #262730 !important;
            border: 1px solid #404040 !important;
            border-radius: 0.5rem !important;
            padding: 1rem !important;
        }
        .stTextInput > div > div > input,
        .stNumberInput > div > div > input,
        .stSelectbox > div > div,
        .stMultiSelect > div > div,
        .stTextArea > div > div > textarea {
            background-color: #404040 !important;
            color: #FAFAFA !important;
            border-color: #666666 !important;
        }
        .stFileUploader {
            background-color: #262730 !important;
            border: 1px solid #404040 !important;
            border-radius: 0.5rem !important;
        }
        </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <style>
        .stApp {
            background-color: #FFFFFF !important;
            color: #262730 !important;
        }
        .stSidebar {
            background-color: #F0F2F6 !important;
        }
        .stMetric {
            background-color: #FFFFFF !important;
            padding: 1rem !important;
            border-radius: 0.5rem !important;
            border: 1px solid #E0E0E0 !important;
        }
        .stForm {
            background-color: #FFFFFF !important;
            border: 1px solid #E0E0E0 !important;
            border-radius: 0.5rem !important;
            padding: 1rem !important;
        }
        </style>
        """, unsafe_allow_html=True)

def get_theme_mode():
    """Get the current theme mode from session state."""
    return st.session_state.get('theme_mode', 'Claro')

def setup_theme_selector():
    """Setup the theme selector in the sidebar."""
    with st.sidebar:
        st.subheader("⚙️ Configurações")
        theme_mode = st.selectbox(
            "Modo do tema:",
            ["Claro", "Escuro"],
            key="theme_selector",
            index=0 if st.session_state.get('theme_mode', 'Claro') == 'Claro' else 1
        )
        
        # Store theme in session state
        st.session_state.theme_mode = theme_mode
        
        # Apply CSS
        apply_theme_css()
        
        st.markdown("---")
        
        return theme_mode