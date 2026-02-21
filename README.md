# Dr. KAI - AI Medical Assistant

An AI-powered medical assistant that provides evidence-based health information from approved Swedish medical sources only.

## Features

- 🏥 **Evidence-based**: Only uses information from approved Swedish medical websites (1177.se, socialstyrelsen.se, viss.nu, fass.se)
- 🌐 **Multi-language**: Accepts queries in any language and responds in the user's language
- 🔒 **Secure**: API key authentication for external access
- 📚 **Source citations**: Every response includes proper source references
- 🤖 **AI-powered**: Uses GPT-4 with LangChain/LangGraph for intelligent responses

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   uv sync
   ```

3. Copy environment variables:
   ```bash
   cp .env.example .env
   ```

4. Add your API keys to `.env`:
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `SERPAPI_API_KEY`: Your SerpAPI key for web searches
   - `DR_KAI_API_KEY`: Secure API key for accessing the API endpoints

## Running the API

### Start the Server

```bash
uv run uvicorn api:app --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

#### API Documentation

Once the server is running, you can access:
- **Interactive API docs**: http://localhost:8000/docs
- **OpenAPI schema**: http://localhost:8000/openapi.json

### Test the API

Run the test script to verify functionality:

```bash
uv run python test_api.py
```

This will test:
- Health check endpoint
- Medical queries in multiple languages (English, Swedish, Spanish)
- API key authentication
- Conversation context

#### API Endpoints

- `GET /` - Health check
- `GET /health` - Detailed health status
- `POST /api/medical-query` - Process medical queries
- `DELETE /api/conversation/{conversation_id}` - Clear conversation history

#### API Usage Example

```python
import requests

# Set your API key
headers = {
    "Authorization": f"Bearer your-dr-kai-api-key",
    "Content-Type": "application/json"
}

# Make a query
response = requests.post(
    "http://localhost:8000/api/medical-query",
    json={"query": "What should I do if my shoulder hurts when I raise my arm?"},
    headers=headers
)

print(response.json())
```

#### Response Format

```json
{
  "response": "Based on information from 1177.se, shoulder pain when raising your arm could indicate several conditions including impingement syndrome, rotator cuff issues, or frozen shoulder...",
  "conversation_id": "conv_abc123def456",
  "sources_used": [
    "https://www.1177.se/sjukdomar--besvar/liv--halsa/skelett-leder-och-muskler/axlar/",
    "https://www.1177.se/sjukdomar--besvar/liv--halsa/skelett-leder-och-muskler/axelskada/"
  ],
  "user_language": "English"
}
```

## Medical Sources

Dr. KAI only searches and provides information from these approved Swedish medical sources:

- **1177.se**: Swedish healthcare information portal
- **socialstyrelsen.se**: National Board of Health and Welfare
- **viss.nu**: Medical information from pharmaceutical companies
- **fass.se**: Swedish drug information database

## Important Disclaimer

⚠️ **Dr. KAI is not a doctor and does not replace professional medical advice.**

- This AI assistant provides general health information for educational purposes only
- Always consult healthcare professionals for medical advice, diagnosis, or treatment
- In case of medical emergencies, call emergency services immediately
- The information provided is based on approved Swedish medical sources but should not be used as a substitute for professional medical care

## Architecture

- **Frontend**: FastAPI web framework
- **AI Engine**: LangChain + LangGraph with GPT-4
- **Search**: SerpAPI with domain restrictions
- **Translation**: Multi-language support using Google Translate
- **Authentication**: API key-based security

## Development

### Project Structure

```
├── main.py              # CLI interface and agent setup
├── api.py               # FastAPI application
├── medical_search_tool.py # Medical information search tool
├── web_search.py        # SerpAPI integration
├── translation_utils.py # Language detection and translation
├── pyproject.toml       # Project configuration
└── README.md           # This file
```

### Adding New Medical Sources

To add new approved medical domains, update `APPROVED_MEDICAL_DOMAINS` in `web_search.py`.

## License

This project is for educational and research purposes. Please ensure compliance with all applicable laws and regulations regarding medical information distribution.
