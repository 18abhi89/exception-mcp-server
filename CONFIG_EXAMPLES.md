# Configuration Examples

## Azure OpenAI Credentials - 3 Options

### Option 1: Direct Values in config.yaml (Recommended for Team Deployment)

**Best for:** Single team deployment where credentials can be committed to private repo.

Edit `config.yaml`:
```yaml
azure_openai:
  endpoint: "https://your-resource.openai.azure.com/"
  api_key: "abc123yourapikey456def"
  api_version: "2024-02-15-preview"
```

**Advantages:**
- ✅ No environment variables needed
- ✅ Works immediately after `git clone`
- ✅ Team members don't need to configure anything
- ✅ Simple and straightforward

**Run:**
```bash
streamlit run streamlit_app.py  # Just works!
```

---

### Option 2: Environment Variable References in config.yaml

**Best for:** Multiple environments (dev/staging/prod) or shared config files.

Edit `config.yaml`:
```yaml
azure_openai:
  endpoint: "${AZURE_OPENAI_ENDPOINT}"
  api_key: "${AZURE_OPENAI_KEY}"
  api_version: "2024-02-15-preview"
```

**Set environment variables:**
```bash
export AZURE_OPENAI_ENDPOINT='https://your-resource.openai.azure.com/'
export AZURE_OPENAI_KEY='abc123yourapikey456def'
```

**Advantages:**
- ✅ Different credentials per environment
- ✅ Keep secrets out of version control
- ✅ Standard devops practice

**Run:**
```bash
streamlit run streamlit_app.py  # Reads from env vars
```

---

### Option 3: Environment Variables Only (No config.yaml changes)

**Best for:** Quick testing or CI/CD pipelines.

Leave `config.yaml` as-is (with `${AZURE_OPENAI_ENDPOINT}` references).

**Set environment variables:**
```bash
export AZURE_OPENAI_ENDPOINT='https://your-resource.openai.azure.com/'
export AZURE_OPENAI_KEY='abc123yourapikey456def'
```

**Advantages:**
- ✅ No config file changes needed
- ✅ Works well with Docker/Kubernetes
- ✅ CI/CD friendly

**Run:**
```bash
streamlit run streamlit_app.py  # Auto-detects env vars
```

---

## Full config.yaml Example (Direct Values)

```yaml
project:
  name: "trade-ingestion-exceptions"
  description: "Exception analysis framework"

database:
  type: "postgres"
  host: "db.company.internal"  # Direct value
  port: 5432
  database: "trade_db"
  user: "app_user"
  password: "secure_password_here"  # Or use ${DB_PASSWORD}

azure_openai:
  endpoint: "https://company-ai.openai.azure.com/"  # Direct value
  api_key: "your-actual-api-key-here"                # Direct value
  api_version: "2024-02-15-preview"
  models:
    chat: "gpt-4"
    embeddings: "text-embedding-ada-002"

vector_db:
  provider: "chromadb"
  persist_directory: "./chromadb_data"
  collection_name: "resolved_exceptions"
```

---

## Testing Your Configuration

```bash
# Test that config loads correctly
python -c "import yaml; print(yaml.safe_load(open('config.yaml'))['azure_openai'])"

# Test the framework
python test_framework.py

# Should see:
# ✓ PASS - file_structure
# ✓ PASS - config_loading
# ... etc
```

---

## Quick Start (Direct Values)

1. Edit `config.yaml`:
   ```yaml
   azure_openai:
     endpoint: "https://your-resource.openai.azure.com/"
     api_key: "your-api-key"
   ```

2. Run:
   ```bash
   streamlit run streamlit_app.py
   ```

**That's it! No environment variables needed.** ✅
