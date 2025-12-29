# Examples

This directory contains practical examples demonstrating Lexilux usage.

## Examples

### basic_chat.py
A simple example demonstrating basic chat completions:
- Simple chat calls
- System messages
- Usage statistics

**Run:**
```bash
python examples/basic_chat.py
```

### chat_streaming.py
Demonstrates streaming chat completions:
- Real-time response streaming
- Chunk processing
- Usage tracking in streaming mode

**Run:**
```bash
python examples/chat_streaming.py
```

### embedding_demo.py
Examples for text embeddings:
- Single text embedding
- Batch embeddings
- Vector dimensions and usage

**Run:**
```bash
python examples/embedding_demo.py
```

### rerank_demo.py
Comprehensive reranking examples:
- Basic reranking
- Top-k filtering
- Include documents option
- Score sorting rules (positive and negative scores)
- Extra parameters
- OpenAI-compatible mode vs Chat-based mode

**Features demonstrated:**
- Document reranking with various configurations
- Understanding score formats (positive vs negative)
- Automatic sorting based on score type
- Top-k result filtering
- Mode selection (OpenAI vs Chat)

**Run:**
```bash
python examples/rerank_demo.py
```

### tokenizer_demo.py
Examples for tokenization:
- Online tokenization (using API)
- Offline tokenization (using local models)
- Auto mode (fallback to offline if API unavailable)

**Run:**
```bash
python examples/tokenizer_demo.py
```

### real_api_test.py
Real API integration testing script:
- Tests all Lexilux components with real API endpoints
- Requires `test_endpoints.json` configuration file
- Comprehensive testing of Chat, Embed, and Rerank APIs

**Run:**
```bash
python examples/real_api_test.py
```

## Configuration File Format

The `test_endpoints.json` file is used by `real_api_test.py` to configure API endpoints and credentials. This file should be placed in either the `tests/` or `examples/` directory.

### Complete Configuration Schema

```json
{
  "chat": {
    "model": "string (required)",
    "source_model": "string (optional)",
    "api_base": "string (required)",
    "api_key": "string (required)"
  },
  "embed": {
    "model": "string (required)",
    "source_model": "string (optional)",
    "api_base": "string (required)",
    "api_key": "string (required)"
  },
  "rerank": {
    "model": "string (required)",
    "source_model": "string (optional)",
    "api_base": "string (required)",
    "api_key": "string (required)",
    "mode": "string (optional, 'openai' or 'chat', default: 'chat')"
  }
}
```

### Field Descriptions

#### Common Fields (for all services)

- **`model`** (required): The model identifier to use for API calls.
  - Example: `"deepseek-chat"`, `"text-embedding-ada-002"`, `"RerankService"`
  - This is the primary model name used in API requests.

- **`source_model`** (optional): The original/source model name (for tracking purposes).
  - Example: `"deepseek-chat"`, `"EmbeddingService"`
  - Useful when the API uses a different model name internally.
  - If not provided, defaults to the value of `model`.

- **`api_base`** (required): Base URL for the API endpoint.
  - Example: `"https://api.deepseek.com"`, `"http://192.168.0.220:20551/v1"`
  - Should include protocol (`http://` or `https://`), host, and port if needed.
  - For rerank services, the path determines the mode:
    - If ends with `/v1` or contains `/chat/completions`, chat mode is used
    - Otherwise, OpenAI mode is used (unless explicitly set)

- **`api_key`** (required): API key for authentication.
  - Example: `"sk-123456"`, `"sk-d5ad8808d0f54c599f523b4e1d13c82c"`
  - Used in the `Authorization: Bearer <api_key>` header.

#### Rerank-Specific Fields

- **`mode`** (optional): Rerank API mode selection.
  - Values: `"openai"` or `"chat"` (default: `"chat"`)
  - `"openai"`: Uses OpenAI-compatible standard rerank API format
    - Endpoint: `POST {api_base}/rerank`
    - Request format: `{"model": "...", "query": "...", "documents": [...], "top_n": ..., "return_documents": ...}`
    - Response format: `{"results": [{"index": 0, "relevance_score": 0.95, "document": {"text": "..."}}], "usage": {...}}`
  - `"chat"`: Uses chat-based custom rerank API format
    - Endpoint: `POST {api_base}/chat/completions`
    - Request format: `{"model": "...", "messages": [{"role": "user", "content": "{\"query\": ..., \"candidates\": ...}"}]}`
    - Response format: `{"choices": [{"message": {"content": "..."}}], "usage": {...}}`
  - If not specified, defaults to `"chat"` for backward compatibility.

### Example Configuration Files

#### Minimal Configuration

```json
{
  "chat": {
    "model": "deepseek-chat",
    "api_base": "https://api.deepseek.com",
    "api_key": "sk-your-api-key"
  },
  "embed": {
    "model": "text-embedding-ada-002",
    "api_base": "https://api.openai.com/v1",
    "api_key": "sk-your-api-key"
  },
  "rerank": {
    "model": "rerank-model",
    "api_base": "https://api.example.com/v1",
    "api_key": "sk-your-api-key"
  }
}
```

#### Full Configuration with Optional Fields

```json
{
  "chat": {
    "model": "deepseek-chat",
    "source_model": "deepseek-chat",
    "api_base": "https://api.deepseek.com",
    "api_key": "sk-d5ad8808d0f54c599f523b4e1d13c82c"
  },
  "embed": {
    "model": "EmbeddingService",
    "source_model": "EmbeddingService",
    "api_base": "http://192.168.0.220:20553/v1",
    "api_key": "sk-123456"
  },
  "rerank": {
    "model": "RerankService",
    "source_model": "RerankService",
    "api_base": "http://192.168.0.220:20551/v1",
    "api_key": "sk-123456",
    "mode": "chat"
  }
}
```

#### Rerank Configuration Examples

**OpenAI-Compatible Mode (e.g., Jina):**
```json
{
  "rerank_openai": {
    "model": "jina-reranker-v3",
    "api_base": "https://api.jina.ai/v1",
    "api_key": "jina_your-api-key",
    "mode": "openai"
  }
}
```

**DashScope Mode (Alibaba Cloud):**
```json
{
  "rerank_dashscope": {
    "model": "qwen3-rerank",
    "api_base": "https://dashscope.aliyuncs.com/api/v1/services/rerank/text-rerank/text-rerank",
    "api_key": "sk-your-dashscope-api-key",
    "mode": "dashscope"
  }
}
```

**Chat-Based Mode (Custom Service):**
```json
{
  "rerank_chat": {
    "model": "RerankService",
    "api_base": "http://your-service:port/v1",
    "api_key": "sk-your-api-key",
    "mode": "chat"
  }
}
```

### Configuration File Location

The `real_api_test.py` script looks for `test_endpoints.json` in the following locations (in order):

1. `tests/test_endpoints.json` (preferred location)
2. `examples/test_endpoints.json`

The first file found will be used.

### Security Notes

⚠️ **IMPORTANT**: The `test_endpoints.json` file contains sensitive credentials:

1. **Never commit this file to version control**
   - It's already in `.gitignore` to prevent accidental commits
   - Always verify it's not tracked before pushing changes

2. **Use environment variables in production**
   - For production code, use environment variables instead of config files
   - Example:
     ```python
     import os
     rerank = Rerank(
         base_url=os.getenv("RERANK_API_BASE"),
         api_key=os.getenv("RERANK_API_KEY"),
         model=os.getenv("RERANK_MODEL")
     )
     ```

3. **Restrict file permissions**
   - On Unix systems, restrict access: `chmod 600 test_endpoints.json`
   - Only the owner should be able to read/write the file

4. **Use different keys for testing and production**
   - Never use production API keys in test configurations
   - Rotate keys if accidentally exposed

### Creating Your Configuration File

1. **Copy the template:**
   ```bash
   cp examples/test_endpoints.json.template tests/test_endpoints.json
   ```
   (If a template exists, otherwise create from scratch)

2. **Fill in your API credentials:**
   - Replace `"your-api-key"` with your actual API keys
   - Update `api_base` URLs to match your endpoints
   - Set appropriate model names

3. **Verify the file:**
   ```bash
   python -m json.tool tests/test_endpoints.json
   ```
   This will validate the JSON syntax.

4. **Test the configuration:**
   ```bash
   python examples/real_api_test.py
   ```

## Running All Examples

To run all examples (except real API tests which require credentials):

```bash
# Basic examples
python examples/basic_chat.py
python examples/chat_streaming.py
python examples/embedding_demo.py
python examples/rerank_demo.py
python examples/tokenizer_demo.py

# Real API tests (requires configuration)
python examples/real_api_test.py
```

## Understanding Rerank Score Formats

Different rerank APIs may return scores in different formats:

### Positive Scores
- Format: `0.0` to `1.0` or higher
- Rule: **Higher score = Better relevance**
- Example: `0.95 > 0.80 > 0.70`
- Lexilux sorts in **descending order** (highest first)

### Negative Scores
- Format: Negative numbers (e.g., `-3.0`, `-4.0`)
- Rule: **Less negative = Better relevance**
- Example: `-3.0 > -4.0 > -5.0` (because -3.0 is mathematically greater)
- Lexilux sorts in **descending order** (least negative first)

Lexilux automatically detects the score format and applies the correct sorting order.

## Configuration

Most examples use placeholder credentials. To use real APIs:

1. **Use the configuration file** (recommended for testing):
   - Create `test_endpoints.json` as described above
   - Run `python examples/real_api_test.py`

2. **Set environment variables** (recommended for production):
   ```bash
   export LEXILUX_API_KEY="your-api-key"
   export LEXILUX_BASE_URL="https://api.example.com"
   ```

3. **Modify examples directly** (not recommended):
   - Edit the example files with your credentials
   - Only for quick testing, never commit credentials
