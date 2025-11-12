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

                    # Show top 3 similar cases with detailed justification
                    st.markdown("---")
                    st.markdown("### 🎯 Top 3 Similar Historical Cases")
                    st.markdown("*Each case includes a confidence score, detailed justification, and SQL query to retrieve the record*")

                    similar = db.find_similar(
                        error_message=selected_exception['error_message'],
                        exception_type=selected_exception['exception_type'],
                        exception_category=selected_exception['exception_category'],
                        exception_sub_category=selected_exception.get('exception_sub_category', ''),
                        stacktrace=selected_exception.get('trace', ''),
                        n_results=3  # Focus on top 3
                    )

                    if similar:
                        # Store confidence scores for final recommendation
                        confidence_scores = []

                        for i, sim in enumerate(similar, 1):
                            confidence = (1 - sim['distance']) * 100
                            confidence_scores.append(confidence)
                            metadata = sim.get('metadata', {})
                            document = sim.get('document', '')

                            # Confidence indicator
                            if confidence >= 80:
                                confidence_color = "🟢"
                                confidence_label = "High Confidence"
                                confidence_reason = "Very similar stacktrace pattern and exception characteristics"
                            elif confidence >= 60:
                                confidence_color = "🟡"
                                confidence_label = "Medium Confidence"
                                confidence_reason = "Moderate similarity in error patterns and context"
                            else:
                                confidence_color = "🔴"
                                confidence_label = "Low Confidence"
                                confidence_reason = "Partial match - exercise caution when applying this resolution"

                            with st.expander(
                                f"{confidence_color} **Case {i}: {confidence:.1f}% Confidence** - {confidence_label}",
                                expanded=(i == 1)  # Expand first one by default
                            ):
                                # Confidence visualization
                                st.progress(confidence / 100)

                                # Detailed justification
                                st.markdown("#### 📊 Confidence Score Justification")
                                st.info(f"**{confidence:.1f}% Match** - {confidence_reason}")

                                # Matching details
                                st.markdown("**Why this match was selected:**")
                                match_reasons = []

                                # Compare exception types
                                if metadata.get('exception_type') == selected_exception['exception_type']:
                                    match_reasons.append("✓ Identical exception type")
                                else:
                                    match_reasons.append("• Different exception type (may indicate related but distinct issue)")

                                # Compare categories
                                if metadata.get('exception_category') == selected_exception['exception_category']:
                                    match_reasons.append("✓ Same exception category")

                                # Compare sub-categories
                                if metadata.get('exception_sub_category') == selected_exception.get('exception_sub_category', ''):
                                    match_reasons.append("✓ Same exception sub-category")

                                # Stacktrace similarity
                                if selected_exception.get('trace', ''):
                                    match_reasons.append("✓ Semantic similarity in stacktrace patterns")

                                for reason in match_reasons:
                                    st.markdown(f"- {reason}")

                                st.markdown("---")

                                # Exception details
                                st.markdown("#### 📝 Historical Exception Details")
                                col1, col2 = st.columns(2)

                                with col1:
                                    st.markdown(f"**Exception Type:** `{metadata.get('exception_type', 'N/A')}`")
                                    st.markdown(f"**Category:** `{metadata.get('exception_category', 'N/A')}`")
                                    st.markdown(f"**Sub-Category:** `{metadata.get('exception_sub_category', 'N/A')}`")

                                with col2:
                                    st.markdown(f"**Event ID:** `{metadata.get('event_id', 'N/A')}`")
                                    st.markdown(f"**Source System:** `{metadata.get('source_system', 'N/A')}`")
                                    st.markdown(f"**Times Replayed:** `{metadata.get('times_replayed', 'N/A')}`")

                                # Resolution
                                st.markdown("#### ✅ Resolution Applied")
                                resolution = metadata.get('resolution', 'No resolution recorded')
                                if resolution != 'No resolution recorded':
                                    st.success(resolution)
                                else:
                                    st.warning(resolution)

                                # SQL Query in collapsible section
                                st.markdown("---")
                                st.markdown("#### 🔍 Database Query")

                                # Generate SQL query to fetch this specific record
                                exception_id = sim.get('id', 'N/A')
                                event_id = metadata.get('event_id', '')

                                sql_query = f"""-- Query to retrieve this historical exception record
SELECT
    exception_id,
    event_id,
    error_message,
    exception_type,
    exception_category,
    exception_sub_category,
    source_system,
    raising_system,
    times_replayed,
    status,
    trace,
    resolution,
    created_date,
    updated_date
FROM exception_events
WHERE exception_id = '{exception_id}'"""

                                if event_id:
                                    sql_query += f"\n   OR event_id = '{event_id}'"

                                sql_query += ";"

                                with st.expander("📋 Click to view SQL query", expanded=False):
                                    st.code(sql_query, language="sql")
                                    st.caption(f"*Use this query to fetch the complete record from the database*")

                        # Final Recommendation Section
                        st.markdown("---")
                        st.markdown("### 🎯 Final Recommendation")

                        avg_confidence = sum(confidence_scores) / len(confidence_scores)
                        max_confidence = max(confidence_scores)

                        # Determine recommendation based on confidence scores
                        if max_confidence >= 80:
                            rec_icon = "🟢"
                            rec_level = "**HIGH CONFIDENCE RECOMMENDATION**"
                            rec_action = "The top matching case shows strong similarity. The documented resolution is highly likely to resolve this issue."
                        elif max_confidence >= 60:
                            rec_icon = "🟡"
                            rec_level = "**MEDIUM CONFIDENCE RECOMMENDATION**"
                            rec_action = "The matching cases show moderate similarity. Review the resolutions carefully and adapt them to your specific context."
                        else:
                            rec_icon = "🔴"
                            rec_level = "**LOW CONFIDENCE RECOMMENDATION**"
                            rec_action = "Limited similarity found with historical cases. Use these as general guidance but expect to need custom investigation and resolution."

                        st.markdown(f"#### {rec_icon} {rec_level}")
                        st.markdown(f"**Average Confidence:** {avg_confidence:.1f}% | **Best Match:** {max_confidence:.1f}%")

                        st.info(rec_action)

                        # Specific recommended actions
                        st.markdown("#### 📋 Recommended Actions")

                        # Get the best match
                        best_match = similar[0]
                        best_metadata = best_match.get('metadata', {})
                        best_resolution = best_metadata.get('resolution', '')

                        actions = []

                        # Action based on category
                        category = selected_exception['exception_category']
                        times_replayed = int(selected_exception.get('times_replayed', 0))

                        if category == "VALIDATION":
                            actions.append(f"1. **Stop retrying** - This is a VALIDATION error. Retries will not help after {times_replayed} attempts.")
                            actions.append("2. **Investigate data quality** - Check the payload for schema violations or invalid data.")
                            if best_resolution:
                                actions.append(f"3. **Apply historical resolution** - {best_resolution[:150]}...")
                        elif category == "SEQUENCING":
                            actions.append(f"1. **Implement temporal parking** - This is a SEQUENCING error. Retrying indefinitely is not effective after {times_replayed} attempts.")
                            actions.append("2. **Check message order** - Verify if dependent messages have arrived.")
                            if best_resolution:
                                actions.append(f"3. **Apply historical resolution** - {best_resolution[:150]}...")
                        elif category == "BUSINESS_LOGIC":
                            actions.append(f"1. **Review business rules** - Retrying {times_replayed} times won't fix configuration issues.")
                            actions.append("2. **Check reference data** - Verify master data and configuration.")
                            if best_resolution:
                                actions.append(f"3. **Apply historical resolution** - {best_resolution[:150]}...")
                        else:
                            if best_resolution:
                                actions.append(f"1. **Apply historical resolution** - {best_resolution[:150]}...")
                            actions.append(f"2. **Stop futile retries** - After {times_replayed} retries, manual intervention is needed.")
                            actions.append("3. **Investigate root cause** - Use the exception details and similar cases as guidance.")

                        for action in actions:
                            st.markdown(action)

                        # Additional context
                        if times_replayed > 10:
                            st.warning(f"⚠️ **Critical:** This exception has been retried {times_replayed} times. Immediate action is required to prevent resource waste and system degradation.")

                        # Link to full analysis
                        st.markdown("---")
                        st.markdown("💡 **Pro Tip:** Use the SQL queries above to investigate similar patterns in your database and identify systemic issues.")

                    else:
                        st.warning("No similar historical cases found. This may be a new type of exception.")
                        st.markdown("### 🎯 Recommendation for New Exception Type")
                        st.info("""
                        Since no similar cases were found:
                        1. **Document thoroughly** - This is a new pattern that should be added to the knowledge base
                        2. **Investigate root cause** - Review stacktrace, payload, and system logs
                        3. **Stop retries if appropriate** - Evaluate if continued retries will help
                        4. **Add resolution** - Once resolved, add this case to exception_history.csv for future reference
                        """)

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
            results = db.find_similar(error_message=query, n_results=3)

            st.markdown(f"**Query:** `{query}`")
            st.markdown(f"**Found {len(results)} similar cases:**")

            for i, result in enumerate(results, 1):
                similarity = (1 - result['distance']) * 100
                metadata = result.get('metadata', {})

                st.markdown(f"**{i}. Similarity: {similarity:.1f}%**")
                st.markdown(f"- Type: {metadata.get('exception_type', 'N/A')}")
                st.markdown(f"- Category: {metadata.get('exception_category', 'N/A')}")
                st.markdown(f"- Resolution: {metadata.get('resolution', 'N/A')[:100]}...")
                st.markdown("---")

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
