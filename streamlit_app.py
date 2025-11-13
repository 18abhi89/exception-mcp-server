#!/usr/bin/env python3
"""
Streamlit UI for Exception Analysis

Simple visualization of exception analysis with ChromaDB-powered similarity search.
"""

import streamlit as st
import pandas as pd
from pathlib import Path
import sys

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from server import (
    get_high_retry_exceptions,
    load_exception_history,
    exception_db,
    analyze_exception_with_history,
    EXCEPTIONS_CSV
)

# Page config
st.set_page_config(
    page_title="Exception Analysis Dashboard",
    page_icon="🔍",
    layout="wide"
)

# Load exception history on startup
@st.cache_resource
def init_database():
    """Initialize exception database."""
    load_exception_history()
    return exception_db

# Initialize
db = init_database()

# Title
st.title("🔍 Exception Analysis Dashboard")
st.markdown("**Powered by ChromaDB Semantic Search**")

# Sidebar
st.sidebar.header("Settings")
retry_threshold = st.sidebar.slider(
    "Retry Threshold",
    min_value=1,
    max_value=10,
    value=5,
    help="Show exceptions with retries greater than this value"
)

# Main content
tab1, tab2 = st.tabs(["📊 High Retry Exceptions", "🔬 Analyze Exception"])

# Tab 1: High Retry Exceptions
with tab1:
    st.header(f"Exceptions with > {retry_threshold} Retries")

    # Get high retry exceptions
    exceptions = get_high_retry_exceptions(threshold=retry_threshold)

    if not exceptions:
        st.info(f"No exceptions found with more than {retry_threshold} retries.")
    else:
        st.success(f"Found **{len(exceptions)}** exceptions requiring attention")

        # Create DataFrame
        df = pd.DataFrame(exceptions)

        # Display summary metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Exceptions", len(df))

        with col2:
            avg_retries = df['times_replayed'].astype(int).mean()
            st.metric("Avg Retries", f"{avg_retries:.1f}")

        with col3:
            open_count = len(df[df['status'] == 'OPEN'])
            st.metric("Open Status", open_count)

        with col4:
            max_retries = df['times_replayed'].astype(int).max()
            st.metric("Max Retries", max_retries)

        st.markdown("---")

        # Display table with key fields
        display_df = df[[
            'exception_id', 'event_id', 'error_message',
            'exception_category', 'times_replayed', 'status',
            'source_system', 'raising_system'
        ]].copy()

        display_df['times_replayed'] = display_df['times_replayed'].astype(int)

        # Color code by category with simple mapping
        category_colors = {
            'VALIDATION': '#ffcccc',
            'SEQUENCING': '#ffffcc',
            'BUSINESS_LOGIC': '#ffebcc'
        }

        def highlight_category(row):
            color = category_colors.get(row['exception_category'], '')
            return [f'background-color: {color}'] * len(row) if color else [''] * len(row)

        st.dataframe(
            display_df.style.apply(highlight_category, axis=1),
            use_container_width=True,
            height=400
        )

# Tab 2: Analyze Exception
with tab2:
    st.header("🔬 Deep Dive Analysis")

    # Get all exceptions for selection
    exceptions = get_high_retry_exceptions(threshold=0)  # Get all

    if exceptions:
        # Create selection dropdown
        exception_options = {
            f"{exc['event_id']} - {exc['error_message'][:50]}...": exc['exception_id']
            for exc in exceptions
        }

        selected_label = st.selectbox(
            "Select an exception to analyze:",
            options=list(exception_options.keys())
        )

        if selected_label:
            exception_id = exception_options[selected_label]

            # Find the full exception
            selected_exception = next(
                exc for exc in exceptions
                if exc['exception_id'] == exception_id
            )

            # Display exception details
            st.markdown("### Exception Details")

            col1, col2 = st.columns(2)

            with col1:
                st.markdown(f"**Event ID:** `{selected_exception['event_id']}`")
                st.markdown(f"**Exception ID:** `{selected_exception['exception_id']}`")
                st.markdown(f"**Category:** {selected_exception['exception_category']}")
                st.markdown(f"**Type:** {selected_exception['exception_type']}")

            with col2:
                st.markdown(f"**Times Replayed:** {selected_exception['times_replayed']}")
                st.markdown(f"**Status:** {selected_exception['status']}")
                st.markdown(f"**Source:** {selected_exception['source_system']}")
                st.markdown(f"**Raising System:** {selected_exception['raising_system']}")

            st.markdown(f"**Error Message:**")
            st.error(selected_exception['error_message'])

            if selected_exception.get('comment'):
                st.markdown(f"**Comment:** {selected_exception['comment']}")

            st.markdown("---")

            # Show SQL query in collapsible section
            with st.expander("📋 SQL Query for Top 3 Similar Records"):
                st.markdown("**PostgreSQL Query to fetch similar historical exceptions:**")

                # Escape single quotes for SQL
                error_msg = selected_exception.get('error_message', '').replace("'", "''")
                exc_type = selected_exception.get('exception_type', '')
                exc_category = selected_exception.get('exception_category', '')
                exc_sub_category = selected_exception.get('exception_sub_category', '')

                sql_query = f"""SELECT
    exception_id,
    event_id,
    error_message,
    exception_type,
    exception_category,
    exception_sub_category,
    resolution,
    similarity_score
FROM (
    SELECT
        eh.*,
        (
            -- Text similarity using pg_trgm extension
            SIMILARITY(eh.error_message, '{error_msg[:100]}') * 0.4 +
            SIMILARITY(eh.trace, '{selected_exception.get('trace', '')[:100]}') * 0.6 +
            -- Exact match bonuses
            CASE WHEN eh.exception_type = '{exc_type}' THEN 0.2 ELSE 0 END +
            CASE WHEN eh.exception_category = '{exc_category}' THEN 0.15 ELSE 0 END +
            CASE WHEN eh.exception_sub_category = '{exc_sub_category}' THEN 0.1 ELSE 0 END
        ) AS similarity_score
    FROM exception_history eh
    WHERE
        eh.resolution IS NOT NULL
        AND eh.resolution != ''
        -- Filter for same category for better relevance
        AND eh.exception_category = '{exc_category}'
) ranked
WHERE similarity_score > 0.3
ORDER BY similarity_score DESC
LIMIT 3;"""

                st.code(sql_query, language="sql")
                st.markdown("""
                **Query Explanation:**
                - Uses PostgreSQL `pg_trgm` extension for text similarity
                - Weighs stacktrace (60%) more than error message (40%)
                - Adds bonus points for exact matches on type/category
                - Filters for same exception_category for relevance
                - Returns top 3 with similarity score > 0.3
                """)

            # Analyze button
            if st.button("🔍 Analyze Exception", type="primary"):
                with st.spinner("Analyzing..."):
                    analysis = analyze_exception_with_history(selected_exception)
                    st.markdown(analysis)

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("""
### About
Exception Analysis Dashboard using:
- **ChromaDB** for semantic search
- **MCP Server** for tool integration
- **Streamlit** for visualization

Find similar exceptions and their resolutions
to stop futile retries and resolve issues faster.
""")
