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
tab1, tab2, tab3 = st.tabs(["📊 High Retry Exceptions", "🔬 Analyze Exception", "📚 Historical Database"])

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

        # Color code by category
        def highlight_category(row):
            category = row['exception_category']
            if category == 'VALIDATION':
                return ['background-color: #ffcccc'] * len(row)
            elif category == 'SEQUENCING':
                return ['background-color: #ffffcc'] * len(row)
            elif category == 'BUSINESS_LOGIC':
                return ['background-color: #ffebcc'] * len(row)
            else:
                return [''] * len(row)

        st.dataframe(
            display_df.style.apply(highlight_category, axis=1),
            use_container_width=True,
            height=400
        )

        # Category breakdown
        st.markdown("### 📈 Category Breakdown")
        col1, col2 = st.columns(2)

        with col1:
            category_counts = df['exception_category'].value_counts()
            st.bar_chart(category_counts)

        with col2:
            st.markdown("**Legend:**")
            st.markdown("🔴 VALIDATION - Data/schema issues (retries won't help)")
            st.markdown("🟡 SEQUENCING - Out-of-order messages (may need temporal parking)")
            st.markdown("🟠 BUSINESS_LOGIC - Configuration/reference data issues")
            st.markdown("🔵 INFRASTRUCTURE - Service/network issues (transient)")

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

            # Analyze button
            if st.button("🔍 Analyze with Historical Data", type="primary"):
                with st.spinner("Analyzing exception and finding similar cases..."):
                    # Perform analysis
                    analysis = analyze_exception_with_history(selected_exception)

                    # Display analysis
                    st.markdown("### 📋 Analysis Results")
                    st.markdown(analysis)

                    # Show similar cases with confidence scores
                    st.markdown("---")
                    st.markdown("### 🎯 Similar Historical Cases (High Confidence > 70%)")

                    similar = db.find_similar(
                        error_message=selected_exception['error_message'],
                        exception_type=selected_exception['exception_type'],
                        exception_category=selected_exception['exception_category'],
                        n_results=10  # Get more results to increase chance of finding high-confidence matches
                    )

                    # Filter for high confidence matches (> 70%)
                    high_confidence_matches = []
                    if similar:
                        for sim in similar:
                            confidence = (1 - sim['distance']) * 100
                            if confidence > 70:
                                high_confidence_matches.append((sim, confidence))

                    if high_confidence_matches:
                        st.success(f"Found {len(high_confidence_matches)} high-confidence match(es) (> 70% similarity)")

                        for i, (sim, confidence) in enumerate(high_confidence_matches, 1):
                            metadata = sim.get('metadata', {})

                            # Confidence indicator (now all are high confidence)
                            if confidence >= 80:
                                confidence_color = "🟢"
                                confidence_label = "Very High Confidence"
                            else:
                                confidence_color = "🟡"
                                confidence_label = "High Confidence"

                            with st.expander(
                                f"{confidence_color} Case {i}: {confidence:.1f}% Similar - {confidence_label}",
                                expanded=(i == 1)  # Expand first one
                            ):
                                st.progress(max(0.0, min(1.0, confidence / 100)))

                                st.markdown(f"**Exception Type:** {metadata.get('exception_type', 'N/A')}")
                                st.markdown(f"**Category:** {metadata.get('exception_category', 'N/A')}")
                                st.markdown(f"**Event ID:** {metadata.get('event_id', 'N/A')}")

                                st.markdown("**Resolution:**")
                                st.success(metadata.get('resolution', 'No resolution recorded'))
                    else:
                        st.warning("No high-confidence matches found (> 70% similarity). This may be a new type of exception or require manual investigation.")

# Tab 3: Historical Database
with tab3:
    st.header("📚 Historical Exception Database")

    st.markdown(f"""
    **Total Historical Records:** {db.count()}

    This database contains resolved exceptions with documented resolutions,
    used for semantic similarity search to suggest fixes for current issues.
    """)

    # Show sample searches
    st.markdown("### 🔎 Try Similarity Search")

    sample_queries = [
        "DELETE operation on non-existent trade",
        "Schema validation failed missing field",
        "Unsupported event type",
        "Settlement date calculation failed"
    ]

    query = st.selectbox("Sample queries:", sample_queries)

    if st.button("Search"):
        with st.spinner("Searching..."):
            results = db.find_similar(error_message=query, n_results=10)

            # Filter for high confidence results (> 70%)
            high_confidence_results = []
            for result in results:
                similarity = (1 - result['distance']) * 100
                if similarity > 70:
                    high_confidence_results.append((result, similarity))

            st.markdown(f"**Query:** `{query}`")

            if high_confidence_results:
                st.markdown(f"**Found {len(high_confidence_results)} high-confidence match(es) (> 70% similarity):**")

                for i, (result, similarity) in enumerate(high_confidence_results, 1):
                    metadata = result.get('metadata', {})

                    # Color code based on confidence
                    if similarity >= 80:
                        st.markdown(f"**{i}. 🟢 Similarity: {similarity:.1f}% (Very High)**")
                    else:
                        st.markdown(f"**{i}. 🟡 Similarity: {similarity:.1f}% (High)**")

                    st.markdown(f"- Type: {metadata.get('exception_type', 'N/A')}")
                    st.markdown(f"- Category: {metadata.get('exception_category', 'N/A')}")
                    st.markdown(f"- Resolution: {metadata.get('resolution', 'N/A')[:100]}...")
                    st.markdown("---")
            else:
                st.warning(f"No high-confidence matches found (> 70% similarity) for query: '{query}'")

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
