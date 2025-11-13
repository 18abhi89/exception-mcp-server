#!/usr/bin/env python3
"""
Simple Streamlit UI for Exception Analysis

Shows how the AI-powered exception analysis framework works.
"""

import streamlit as st
import pandas as pd
import csv
import os
import yaml
from pathlib import Path

from llm_client import AzureOpenAIClient
from vector_store import ExceptionVectorStore

# Page config
st.set_page_config(
    page_title="Exception Analysis Framework",
    page_icon="🔍",
    layout="wide"
)

# Paths
DATA_DIR = Path(__file__).parent / "data"
CSV_PATH = DATA_DIR / "exceptions.csv"
VECTOR_DB_PATH = "./chromadb_data"
CONFIG_FILE = Path(__file__).parent / "config.yaml"


def get_config_value(config_value: str, env_fallback: str = None) -> str:
    """
    Get configuration value, supporting both direct values and ${ENV_VAR} substitution.

    Args:
        config_value: Value from config (can be direct value or ${ENV_VAR})
        env_fallback: Environment variable name to check as fallback

    Returns:
        Resolved value or None
    """
    if config_value:
        # Check if it's an environment variable reference
        if config_value.startswith("${") and config_value.endswith("}"):
            env_var = config_value[2:-1]
            # Support default values: ${VAR:default}
            if ':' in env_var:
                var_name, default = env_var.split(':', 1)
                return os.getenv(var_name, default)
            return os.getenv(env_var)
        # Direct value
        return config_value

    # Fallback to environment variable
    if env_fallback:
        return os.getenv(env_fallback)

    return None


@st.cache_resource
def initialize_clients():
    """Initialize AI clients."""
    # Load config
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r') as f:
            config = yaml.safe_load(f)

        # Get credentials from config (supports direct values or ${ENV_VAR})
        endpoint = get_config_value(
            config['azure_openai'].get('endpoint'),
            'AZURE_OPENAI_ENDPOINT'
        )
        api_key = get_config_value(
            config['azure_openai'].get('api_key'),
            'AZURE_OPENAI_KEY'
        )
    else:
        # Fallback to environment variables
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        api_key = os.getenv("AZURE_OPENAI_KEY")

    if not endpoint or not api_key:
        return None, None

    llm_client = AzureOpenAIClient(endpoint=endpoint, api_key=api_key)
    vector_store = ExceptionVectorStore(
        llm_client=llm_client,
        persist_directory=VECTOR_DB_PATH
    )

    return llm_client, vector_store


@st.cache_data
def load_exceptions():
    """Load exceptions from CSV."""
    if not CSV_PATH.exists():
        return []

    exceptions = []
    with open(CSV_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            exceptions.append(row)

    return exceptions


# Initialize
llm_client, vector_store = initialize_clients()
all_exceptions = load_exceptions()

# Title
st.title("🔍 Exception Analysis Framework")
st.markdown("**AI-powered exception analysis with vector similarity search**")

# Check if AI is available
if not llm_client:
    st.warning("⚠️ Azure OpenAI credentials not configured. Edit `config.yaml` and paste your endpoint and API key.")

# Tabs
tab1, tab2 = st.tabs(["📊 High Retry Exceptions", "🤖 AI Analysis"])

# Tab 1: High Retry Exceptions
with tab1:
    st.header("High Retry Exceptions")

    # Filter settings
    col1, col2 = st.columns([1, 3])
    with col1:
        retry_threshold = st.slider(
            "Minimum Retries",
            min_value=1,
            max_value=20,
            value=5
        )

    # Filter exceptions
    high_retry = [
        exc for exc in all_exceptions
        if int(exc.get('times_replayed', 0)) >= retry_threshold
    ]

    if not high_retry:
        st.info(f"No exceptions with {retry_threshold}+ retries found")
    else:
        st.success(f"Found **{len(high_retry)}** exceptions")

        # Create DataFrame
        df = pd.DataFrame(high_retry)

        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total", len(df))
        with col2:
            avg_retries = df['times_replayed'].astype(int).mean()
            st.metric("Avg Retries", f"{avg_retries:.1f}")
        with col3:
            open_count = len(df[df['status'] == 'OPEN'])
            st.metric("Open", open_count)
        with col4:
            closed_count = len(df[df['status'] == 'CLOSED'])
            st.metric("Closed", closed_count)

        st.markdown("---")

        # Display table
        display_df = df[[
            'exception_id', 'event_id', 'error_message',
            'exception_type', 'exception_category', 'status',
            'times_replayed', 'source_system'
        ]].copy()

        display_df['times_replayed'] = display_df['times_replayed'].astype(int)

        # Color coding
        def highlight_status(row):
            if row['status'] == 'OPEN':
                return ['background-color: #ffcccc'] * len(row)
            return ['background-color: #ccffcc'] * len(row)

        st.dataframe(
            display_df.style.apply(highlight_status, axis=1),
            use_container_width=True,
            height=400
        )

# Tab 2: AI Analysis
with tab2:
    st.header("🤖 AI-Powered Exception Analysis")

    if not llm_client or not vector_store:
        st.error("❌ AI clients not initialized. Edit `config.yaml` with your Azure OpenAI credentials and refresh page.")
    else:
        # Vector DB stats
        vector_count = vector_store.count()
        if vector_count == 0:
            st.warning(f"⚠️ Vector database is empty. Run `python ingest.py` to load resolved exceptions.")
        else:
            st.info(f"📊 Vector database contains {vector_count} resolved exceptions")

        st.markdown("---")

        # Select exception
        if not all_exceptions:
            st.error("No exceptions found in CSV")
        else:
            # Create dropdown options
            exception_options = {
                f"{exc['event_id']} - {exc['error_message'][:60]}...": exc['exception_id']
                for exc in all_exceptions
            }

            selected_label = st.selectbox(
                "Select an exception to analyze:",
                options=list(exception_options.keys())
            )

            if selected_label:
                exception_id = exception_options[selected_label]

                # Find the exception
                selected_exception = next(
                    exc for exc in all_exceptions
                    if exc['exception_id'] == exception_id
                )

                # Display exception details
                st.markdown("### 📋 Exception Details")

                # Key identifiers
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown(f"**Event ID:** `{selected_exception['event_id']}`")
                with col2:
                    st.markdown(f"**Exception ID:** `{selected_exception['exception_id']}`")
                with col3:
                    status_color = "🟢" if selected_exception['status'] == 'CLOSED' else "🔴"
                    st.markdown(f"**Status:** {status_color} {selected_exception['status']}")

                st.markdown("---")

                # Exception classification
                st.markdown("#### 🏷️ Classification")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown(f"**Type:** {selected_exception.get('exception_type', 'N/A')}")
                with col2:
                    st.markdown(f"**Category:** {selected_exception.get('exception_category', 'N/A')}")
                with col3:
                    st.markdown(f"**Sub-Category:** {selected_exception.get('exception_sub_category', 'N/A')}")

                # System information
                st.markdown("#### 🖥️ System Information")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.markdown(f"**Source:** {selected_exception.get('source_system', 'N/A')}")
                with col2:
                    st.markdown(f"**Raising System:** {selected_exception.get('raising_system', 'N/A')}")
                with col3:
                    st.markdown(f"**Host:** {selected_exception.get('host', 'N/A')}")
                with col4:
                    st.markdown(f"**Destination:** {selected_exception.get('destination', 'N/A')}")

                # Event details
                st.markdown("#### 📅 Event Details")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown(f"**Event Type:** {selected_exception.get('event_type', 'N/A')}")
                with col2:
                    st.markdown(f"**Event ID Type:** {selected_exception.get('event_id_type', 'N/A')}")
                with col3:
                    st.markdown(f"**Event Version:** {selected_exception.get('event_version', 'N/A')}")

                # Replay information
                st.markdown("#### 🔄 Replay & Status")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.markdown(f"**Times Replayed:** {selected_exception.get('times_replayed', 0)}")
                with col2:
                    st.markdown(f"**Is Active:** {selected_exception.get('is_active', 'N/A')}")
                with col3:
                    st.markdown(f"**Created:** {selected_exception.get('created_date', 'N/A')}")
                with col4:
                    st.markdown(f"**Updated:** {selected_exception.get('updated_date', 'N/A')}")

                if selected_exception.get('updated_by'):
                    st.markdown(f"**Updated By:** {selected_exception.get('updated_by')}")

                if selected_exception.get('messaging_platform_type'):
                    st.markdown(f"**Messaging Platform:** {selected_exception.get('messaging_platform_type')}")

                st.markdown("---")

                # Error message
                st.markdown("#### ⚠️ Error Message")
                st.error(selected_exception['error_message'])

                # Stack trace
                st.markdown("#### 📚 Stack Trace")
                st.code(selected_exception.get('trace', 'No trace available'), language="text", line_numbers=True)

                # Comments/Remarks
                if selected_exception.get('comment') or selected_exception.get('remarks'):
                    st.markdown("#### 💬 Comments & Remarks")
                    if selected_exception.get('comment'):
                        st.info(f"**Comment:** {selected_exception.get('comment')}")
                    if selected_exception.get('remarks'):
                        st.success(f"**Resolution Remarks:** {selected_exception.get('remarks')}")

                # Payload (if available)
                if selected_exception.get('payload'):
                    with st.expander("📦 View Payload"):
                        st.code(selected_exception.get('payload'), language="json")

                st.markdown("---")

                # AI Generated Resolution placeholder
                st.markdown("#### 🤖 AI Generated Resolution")
                with st.container():
                    st.info("""
                    **Resolution Status:** Pending Analysis

                    Click the "🔍 Analyze with AI" button below to generate an AI-powered resolution recommendation based on:
                    - Similar historical exceptions
                    - Stack trace analysis
                    - Root cause identification
                    - Recommended fixes with citations
                    """)

                st.markdown("---")

                # Analyze button
                if st.button("🔍 Analyze with AI", type="primary", use_container_width=True):
                    if vector_count == 0:
                        st.error("Cannot analyze: Vector database is empty. Run `python ingest.py` first.")
                    else:
                        # Clear the placeholder and show analysis
                        st.markdown("---")

                        with st.spinner("🔍 Finding similar exceptions..."):
                            # Find similar
                            similar = vector_store.find_similar(
                                exception_id,
                                selected_exception,
                                top_k=3
                            )

                        with st.spinner("🤖 Generating AI-powered resolution..."):
                            # Get schema
                            schema = "Database schema for trade_ingestion_exception table"

                            # Generate analysis
                            analysis = llm_client.analyze_exception(
                                selected_exception,
                                similar,
                                schema
                            )

                        # Display AI Generated Resolution (replaces placeholder)
                        st.markdown("### 🤖 AI Generated Resolution")

                        # Resolution content
                        with st.container():
                            st.success("**Resolution Status:** ✅ Analysis Complete")
                            st.markdown(analysis)

                        st.markdown("---")

                        # Citations section
                        if similar:
                            st.markdown("### 📚 Citations - Similar Historical Cases")
                            st.caption("The AI analysis above is based on the following resolved exceptions:")

                            for i, sim in enumerate(similar, 1):
                                metadata = sim.get('metadata', {})
                                similarity = sim.get('similarity', 0) * 100

                                with st.expander(f"📖 Citation [{i}] - {similarity:.1f}% similarity match", expanded=False):
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        st.markdown(f"**Exception Type:** {metadata.get('exception_type', 'N/A')}")
                                        st.markdown(f"**Category:** {metadata.get('exception_category', 'N/A')}")
                                        st.markdown(f"**Sub-Category:** {metadata.get('exception_sub_category', 'N/A')}")
                                    with col2:
                                        st.markdown(f"**Source System:** {metadata.get('source_system', 'N/A')}")
                                        st.markdown(f"**Raising System:** {metadata.get('raising_system', 'N/A')}")
                                        st.markdown(f"**Similarity Score:** {similarity:.2f}%")

                                    st.markdown("**Error Message:**")
                                    st.text(metadata.get('error_message', 'N/A'))

                                    st.markdown("**Resolution Applied:**")
                                    resolution = metadata.get('remarks', 'No resolution remarks available')
                                    st.info(resolution)

                                    if metadata.get('exception_id'):
                                        st.caption(f"Exception ID: `{metadata.get('exception_id')}`")
                        else:
                            st.warning("⚠️ No similar historical cases found. The AI analysis above is based on general exception patterns and best practices.")

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("""
### About

This framework demonstrates:
- **Vector similarity search** using ChromaDB
- **AI-powered analysis** with Azure OpenAI
- **Simple architecture** that works across projects

### Setup
1. Edit `config.yaml`:
   - Paste your Azure OpenAI endpoint
   - Paste your API key
2. Run `python ingest.py` to load data
3. Run `streamlit run streamlit_app.py`
""")
