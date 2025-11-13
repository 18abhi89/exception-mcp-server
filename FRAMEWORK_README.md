# Exception Analysis Framework

**AI-powered exception analysis framework for operations teams.**

Simple, testable framework that uses vector similarity search and LLM analysis to help ops teams resolve production exceptions faster.

---

## 🎯 What This Framework Does

1. **Loads exception data** from your database/CSV
2. **Ingests resolved exceptions** into vector database (ChromaDB)
3. **Finds similar cases** using AI embeddings (Azure OpenAI)
4. **Generates analysis** with root cause and recommendations
5. **Provides MCP tools** for Claude integration
6. **Simple UI** to visualize the workflow

---

## 📁 Project Structure

```
exception-mcp-server/
├── config.yaml                    # Configuration (schema, Azure OpenAI, etc.)
├── llm_client.py                  # Azure OpenAI client (uses requests)
├── stacktrace_parser.py           # Parse Java stack traces
├── vector_store.py                # ChromaDB wrapper with embeddings
├── server_new.py                  # MCP server with AI tools
├── streamlit_app_new.py           # Simple UI
├── ingest.py                      # Load resolved exceptions into vector DB
├── generate_sample_data.py        # Generate test data
├── test_framework.py              # Comprehensive tests
├── data/
│   └── exceptions.csv             # Exception data (100 sample records)
└── requirements.txt               # Dependencies
```

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Azure OpenAI Credentials

```bash
export AZURE_OPENAI_ENDPOINT='https://your-resource.openai.azure.com/'
export AZURE_OPENAI_KEY='your-api-key-here'
```

### 3. Run Tests

```bash
python test_framework.py
```

Expected output:
```
Results: 7/7 tests passed
✓ All tests passed!
```

### 4. Ingest Data into Vector Database

```bash
python ingest.py
```

This loads all CLOSED exceptions (with remarks) into ChromaDB for similarity search.

### 5. Run the UI

```bash
streamlit run streamlit_app_new.py
```

Open browser at `http://localhost:8501`

---

## 🔧 Configuration

### config.yaml

The framework uses a single configuration file. Key sections:

#### 1. Database Connection
```yaml
database:
  type: "postgres"
  host: "${DB_HOST:localhost}"
  port: 5432
  database: "${DB_NAME:trade_db}"
  user: "${DB_USER:postgres}"
  password: "${DB_PASSWORD:postgres}"
```

#### 2. Azure OpenAI
```yaml
azure_openai:
  endpoint: "${AZURE_OPENAI_ENDPOINT}"
  api_key: "${AZURE_OPENAI_KEY}"
  models:
    chat: "gpt-4"
    embeddings: "text-embedding-ada-002"
```

#### 3. Schema (Copy-Paste from Your DB)
```yaml
schema:
  trade_ingestion_exception: |
    CREATE TABLE trade_ingestion_exception (
        id BIGSERIAL PRIMARY KEY,
        exception_id UUID,
        error_message TEXT,
        exception_type VARCHAR(255),
        trace TEXT,
        status VARCHAR(255),
        remarks TEXT,
        ...
    );
```

**Just copy your CREATE TABLE statement - no need to manually define each field!**

---

## 📊 Data Requirements

### Required Columns

Your exception table must have:

| Column | Type | Required | Purpose |
|--------|------|----------|---------|
| `exception_id` | UUID/VARCHAR | Yes | Unique identifier |
| `error_message` | TEXT | Yes | Error description |
| `exception_type` | VARCHAR | Yes | Exception class (e.g., NullPointerException) |
| `exception_category` | VARCHAR | Yes | Category (VALIDATION, INFRASTRUCTURE, etc.) |
| `trace` | TEXT | Yes | Stack trace |
| `status` | VARCHAR | Yes | OPEN or CLOSED |
| `remarks` | TEXT | For CLOSED | How it was resolved |
| `times_replayed` | INTEGER | Optional | Retry count |
| `source_system` | VARCHAR | Optional | Source system |

### Single Table Design

**No separate history table needed!**

- OPEN exceptions = current issues
- CLOSED exceptions with remarks = historical resolutions

Vector DB only ingests `WHERE status='CLOSED' AND remarks IS NOT NULL`

---

## 🧪 Testing Framework

### Run All Tests

```bash
python test_framework.py
```

### What Gets Tested

1. ✅ **File Structure** - All required files exist
2. ✅ **Configuration** - Config loads and has required keys
3. ✅ **CSV Data** - Data loads with correct fields
4. ✅ **Stacktrace Parser** - Parses method chains correctly
5. ✅ **LLM Client** - Client structure is correct
6. ✅ **Vector Store** - Vector store structure is correct
7. ✅ **Environment** - Azure credentials are set

### Test Output

```
================================================================================
TEST SUMMARY
================================================================================
PASS - file_structure
PASS - config_loading
PASS - csv_data
PASS - stacktrace_parser
PASS - llm_client_structure
PASS - vector_store_structure
PASS - environment_variables
================================================================================
Results: 7/7 tests passed
✓ All tests passed!
```

---

## 🎮 Using the Framework

### Option 1: Streamlit UI

```bash
streamlit run streamlit_app_new.py
```

**Tab 1: High Retry Exceptions**
- View exceptions with high retry counts
- Filter by retry threshold
- Color-coded by status (OPEN/CLOSED)

**Tab 2: AI Analysis**
- Select an exception
- Click "Analyze with AI"
- See similar historical cases
- Get AI-generated root cause analysis

### Option 2: MCP Server

```bash
python server_new.py
```

**Available Tools:**
1. `getSchema()` - Get database schema
2. `querySafeSQL(sql)` - Execute SELECT queries
3. `findSimilarExceptions(exception_id, top_k)` - Find similar cases
4. `analyzeExceptionWithAI(exception_id)` - Get AI analysis

### Option 3: Python API

```python
from llm_client import AzureOpenAIClient
from vector_store import ExceptionVectorStore

# Initialize
llm_client = AzureOpenAIClient(endpoint, api_key)
vector_store = ExceptionVectorStore(llm_client)

# Find similar exceptions
similar = vector_store.find_similar(exception_id, exception, top_k=3)

# Generate analysis
analysis = llm_client.analyze_exception(exception, similar, schema)
```

---

## 🔄 Adapting for Your Project

### Step 1: Update config.yaml

1. Replace database connection details
2. Copy-paste your CREATE TABLE statement into `schema` section
3. Update table name if different

### Step 2: Generate or Load Your Data

**Option A: Use existing data**
```bash
# Export from your database to CSV
psql -d your_db -c "COPY your_table TO '/path/to/exceptions.csv' CSV HEADER"
```

**Option B: Generate test data**
```bash
# Modify generate_sample_data.py for your exception types
python generate_sample_data.py
```

### Step 3: Run Tests

```bash
python test_framework.py
```

### Step 4: Ingest & Use

```bash
python ingest.py
streamlit run streamlit_app_new.py
```

---

## 📈 How Similarity Search Works

### 1. Embedding Generation

For each exception:
```
text = error_message + exception_type + stacktrace
embedding = azure_openai.embed(text)
```

### 2. Metadata Storage

Stored alongside embedding:
- exception_type
- exception_category
- exception_sub_category
- source_system
- method_chain (parsed from stacktrace)
- remarks (resolution)

### 3. Similarity Search

```python
# Find similar exceptions
similar = vector_store.find_similar(
    exception_id,
    exception_record,
    top_k=3,
    filter_category=True  # Only search same category
)
```

### 4. AI Analysis

```python
# LLM generates analysis
analysis = llm_client.analyze_exception(
    exception,       # Current exception
    similar_cases,   # Top 3 similar
    schema          # DB schema for context
)
```

---

## 🛠 Troubleshooting

### Tests Failing

**"chromadb module not found"**
```bash
pip install -r requirements.txt
```

**"Azure credentials not set"**
```bash
export AZURE_OPENAI_ENDPOINT='your-endpoint'
export AZURE_OPENAI_KEY='your-key'
```

### Vector DB Empty

```bash
# Check if you have CLOSED exceptions with remarks
python -c "import csv; print(sum(1 for r in csv.DictReader(open('data/exceptions.csv')) if r['status']=='CLOSED' and r['remarks']))"

# Re-run ingestion
python ingest.py
```

### No Similar Exceptions Found

- Ensure vector DB is loaded (`python ingest.py`)
- Check that exceptions are in same category
- Verify stack traces have common method chains

---

## 🎯 Key Design Decisions

### Why ChromaDB?
- Simple file-based storage
- No separate database server needed
- Easy to deploy per-team

### Why Single Table?
- Simpler schema
- No joins needed
- Just filter by status='CLOSED'

### Why Azure OpenAI?
- Enterprise-ready
- Good embedding quality (Ada-002)
- Simple REST API

### Why Copy-Paste Schema?
- No manual field definitions
- Works with any schema
- Framework parses it automatically

---

## 📝 Next Steps

1. **Test with your data** - Replace sample CSV with real exceptions
2. **Tune similarity** - Adjust filtering and top_k values
3. **Customize UI** - Modify streamlit_app_new.py for your needs
4. **Add monitoring** - Track analysis quality and usage

---

## 💡 Pro Tips

1. **Batch ingest** - Run `python ingest.py` daily/weekly to keep vector DB updated
2. **Filter by category** - Keeps similarity search relevant
3. **Good remarks** - Quality of resolution notes = quality of recommendations
4. **Common method chains** - Exceptions with similar stack traces cluster well

---

## 🤝 Support

For issues or questions:
1. Run `python test_framework.py` to diagnose
2. Check configuration in `config.yaml`
3. Verify Azure OpenAI credentials
4. Ensure vector DB is loaded

---

**Framework is ready to use! Run tests and start analyzing exceptions.** 🚀
