# Gemini RAG with File Search API

A production-ready RAG (Retrieval Augmented Generation) application using Google's Gemini File Search API with FastAPI backend and modern web interface.

## Features

- 🔍 **Semantic Search** - Find relevant information using AI-powered semantic search
- 📚 **Citation Support** - Get accurate citations and source references
- 📄 **Multiple File Formats** - Support for PDF, TXT, DOCX, MD, JSON, CSV, and more
- 🎨 **Modern UI** - Beautiful glassmorphism design with dark mode
- ⚡ **Fast Retrieval** - Optimized chunking and indexing for quick responses
- 🏪 **Store Management** - Create and manage multiple File Search stores
- 🎯 **Metadata Filtering** - Filter documents using custom metadata

## Prerequisites

- Python 3.8+
- Google AI API Key ([Get one here](https://aistudio.google.com/app/apikey))

## Installation

1. **Clone or navigate to the project directory**:
   ```bash
   cd "C:\Users\DELL\OneDrive\Desktop\Upwork Projects\GeminiFileSearch"
   ```

2. **Activate virtual environment**:
   ```bash
   .\venv\Scripts\Activate.ps1
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   - Copy `.env.example` to `.env`
   - Add your Gemini API key:
     ```
     GEMINI_API_KEY=your_api_key_here
     ```

## Usage

1. **Start the server**:
   ```bash
   python main.py
   ```
   Or with uvicorn:
   ```bash
   uvicorn main:app --reload
   ```

2. **Open your browser**:
   Navigate to `http://localhost:8000`

3. **Create a File Search Store**:
   - Click "Create Store" button
   - Enter a descriptive name
   - Click "Create"

4. **Upload Documents**:
   - Select a store from the sidebar
   - Drag & drop files or click to browse
   - Wait for indexing to complete

5. **Ask Questions**:
   - Type your question in the chat input
   - Get AI-powered answers with citations
   - View source references for verification

## API Endpoints

### Store Management
- `POST /api/stores/create` - Create a new File Search store
- `GET /api/stores/list` - List all stores
- `DELETE /api/stores/{store_id}` - Delete a store

### File Operations
- `POST /api/files/upload` - Upload and index a file

### Query
- `POST /api/query` - Query documents with File Search

## Supported File Types

- **Documents**: PDF, DOCX, DOC, TXT, MD, RTF
- **Data**: JSON, CSV, TSV, XML
- **Code**: PY, JS, TS, JAVA, CPP, GO, RS, and more
- **Spreadsheets**: XLSX, XLS
- **Presentations**: PPTX

See [Gemini File Search documentation](https://ai.google.dev/gemini-api/docs/file-search) for complete list.

## Pricing

- **Embeddings**: $0.15 per 1M tokens (at indexing time)
- **Storage**: Free
- **Query-time embeddings**: Free
- **Model tokens**: Standard Gemini pricing applies

### Free Tier Limits
- Total File Search store size: 1 GB
- Recommended max per store: 20 GB for optimal performance

## Configuration

### Chunking Configuration
Customize chunking in the upload request:
- `max_tokens_per_chunk`: Maximum tokens per chunk (default: 800)
- `max_overlap_tokens`: Overlap between chunks (default: 100)

### Custom Metadata
Add metadata to files for filtering:
```javascript
{
  "metadata": [
    {"key": "author", "string_value": "John Doe"},
    {"key": "year", "numeric_value": 2024}
  ]
}
```

## Troubleshooting

### API Key Issues
- Ensure your API key is valid and active
- Check that `.env` file is in the project root
- Verify the key has File Search API access

### Upload Failures
- Check file size (max 100 MB per file)
- Verify file format is supported
- Ensure store exists and is accessible

### Query Issues
- Verify a store is selected
- Check that files have been successfully indexed
- Review operation completion status

## Development

### Project Structure
```
GeminiFileSearch/
├── main.py              # FastAPI application
├── requirements.txt     # Python dependencies
├── .env                 # Environment variables
├── static/
│   ├── index.html      # Frontend HTML
│   ├── style.css       # Styles
│   └── app.js          # JavaScript logic
└── README.md           # This file
```

### Running in Development Mode
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## License

MIT License - feel free to use this project for your own purposes.

## Resources

- [Gemini File Search Documentation](https://ai.google.dev/gemini-api/docs/file-search)
- [Google AI Studio](https://aistudio.google.com/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
