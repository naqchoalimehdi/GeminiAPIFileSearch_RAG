import os
import time
import traceback
from typing import Optional, List
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from google import genai
from google.genai import types
import tempfile
import json

# Load environment variables
load_dotenv()

# Check for API key
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("\n" + "="*70)
    print("ERROR: GEMINI_API_KEY not found!")
    print("="*70)
    print("\nPlease follow these steps:")
    print("1. Get your API key from: https://aistudio.google.com/app/apikey")
    print("2. Copy .env.example to .env")
    print("3. Add your API key to the .env file:")
    print("   GEMINI_API_KEY=your_api_key_here")
    print("\nThen run the server again.")
    print("="*70 + "\n")
    exit(1)

# Initialize Gemini client
client = genai.Client(api_key=api_key)

# Initialize FastAPI app
app = FastAPI(title="Gemini RAG with File Search", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class CreateStoreRequest(BaseModel):
    display_name: str

class QueryRequest(BaseModel):
    query: str
    store_name: str
    metadata_filter: Optional[str] = None

class MetadataItem(BaseModel):
    key: str
    string_value: Optional[str] = None
    numeric_value: Optional[float] = None

class UploadFileRequest(BaseModel):
    store_name: str
    display_name: str
    metadata: Optional[List[MetadataItem]] = None
    max_tokens_per_chunk: Optional[int] = 800
    max_overlap_tokens: Optional[int] = 100


# Helper function to poll operation
async def wait_for_operation(operation):
    """Poll operation until completion"""
    max_attempts = 60  # 5 minutes max
    attempt = 0
    
    while not operation.done and attempt < max_attempts:
        await asyncio.sleep(5)
        operation = client.operations.get(operation)
        attempt += 1
    
    if not operation.done:
        raise HTTPException(status_code=408, detail="Operation timed out")
    
    return operation


# API Endpoints

@app.get("/")
async def read_root():
    """Serve the main HTML page"""
    return FileResponse("static/index.html")


@app.post("/api/stores/create")
async def create_store(request: CreateStoreRequest):
    """Create a new File Search store"""
    try:
        print(f"Creating store with name: {request.display_name}")
        file_search_store = client.file_search_stores.create(
            config={'display_name': request.display_name}
        )
        print(f"Store created successfully: {file_search_store.name}")
        return {
            "success": True,
            "store": {
                "name": file_search_store.name,
                "display_name": file_search_store.display_name,
                "create_time": str(file_search_store.create_time) if hasattr(file_search_store, 'create_time') else None
            }
        }
    except Exception as e:
        print(f"Error creating store: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to create store: {str(e)}")


@app.get("/api/stores/list")
async def list_stores():
    """List all File Search stores"""
    try:
        print("Listing all stores...")
        stores = []
        for store in client.file_search_stores.list():
            stores.append({
                "name": store.name,
                "display_name": store.display_name,
                "create_time": str(store.create_time) if hasattr(store, 'create_time') else None
            })
        print(f"Found {len(stores)} stores")
        return {"success": True, "stores": stores}
    except Exception as e:
        print(f"Error listing stores: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to list stores: {str(e)}")


@app.delete("/api/stores/{store_id}")
async def delete_store(store_id: str, force: bool = True):
    """Delete a File Search store"""
    try:
        store_name = f"fileSearchStores/{store_id}" if not store_id.startswith("fileSearchStores/") else store_id
        client.file_search_stores.delete(name=store_name, config={'force': force})
        return {"success": True, "message": "Store deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete store: {str(e)}")


@app.post("/api/files/upload")
async def upload_file(
    file: UploadFile = File(...),
    store_name: str = Form(...),
    display_name: str = Form(...),
    metadata: Optional[str] = Form(None),
    max_tokens_per_chunk: int = Form(800),
    max_overlap_tokens: int = Form(100)
):
    """Upload a file directly to File Search store"""
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            # Parse metadata if provided
            custom_metadata = []
            if metadata:
                metadata_list = json.loads(metadata)
                for item in metadata_list:
                    custom_metadata.append(item)
            
            # Upload to File Search store
            config = {
                'display_name': display_name,
                'chunking_config': {
                    'white_space_config': {
                        'max_tokens_per_chunk': max_tokens_per_chunk,
                        'max_overlap_tokens': max_overlap_tokens
                    }
                }
            }
            
            if custom_metadata:
                config['custom_metadata'] = custom_metadata
            
            operation = client.file_search_stores.upload_to_file_search_store(
                file=tmp_file_path,
                file_search_store_name=store_name,
                config=config
            )
            
            # Poll operation until complete
            import asyncio
            max_attempts = 60
            attempt = 0
            
            while not operation.done and attempt < max_attempts:
                await asyncio.sleep(5)
                operation = client.operations.get(operation)
                attempt += 1
            
            if not operation.done:
                raise HTTPException(status_code=408, detail="Upload operation timed out")
            
            return {
                "success": True,
                "message": "File uploaded and indexed successfully",
                "operation": {
                    "name": operation.name,
                    "done": operation.done
                }
            }
        
        finally:
            # Clean up temporary file
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")


@app.post("/api/query")
async def query_documents(request: QueryRequest):
    """Query documents using File Search"""
    max_retries = 3
    retry_delay = 2  # seconds
    
    for attempt in range(max_retries):
        try:
            print(f"Querying store: {request.store_name} with query: {request.query} (attempt {attempt + 1}/{max_retries})")
            
            # Build config
            config = types.GenerateContentConfig(
                tools=[
                    types.Tool(
                        file_search=types.FileSearch(
                            file_search_store_names=[request.store_name]
                        )
                    )
                ]
            )
            
            # Add metadata filter if provided
            if request.metadata_filter:
                config.tools[0].file_search.metadata_filter = request.metadata_filter
            
            # Generate content
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=request.query,
                config=config
            )
            
            print(f"Response received: {response.text[:100]}...")
            
            # Extract grounding metadata and citations
            grounding_metadata = None
            
            if response.candidates and len(response.candidates) > 0:
                candidate = response.candidates[0]
                if hasattr(candidate, 'grounding_metadata') and candidate.grounding_metadata:
                    grounding_metadata = {
                        "grounding_chunks": []
                    }
                    
                    # Check if grounding_chunks exists and is not None
                    if hasattr(candidate.grounding_metadata, 'grounding_chunks') and candidate.grounding_metadata.grounding_chunks:
                        for chunk in candidate.grounding_metadata.grounding_chunks:
                            chunk_data = {}
                            if hasattr(chunk, 'web') and chunk.web:
                                chunk_data['web'] = {
                                    'uri': chunk.web.uri if hasattr(chunk.web, 'uri') else None,
                                    'title': chunk.web.title if hasattr(chunk.web, 'title') else None
                                }
                            if hasattr(chunk, 'retrieved_context') and chunk.retrieved_context:
                                chunk_data['retrieved_context'] = {
                                    'uri': chunk.retrieved_context.uri if hasattr(chunk.retrieved_context, 'uri') else None,
                                    'title': chunk.retrieved_context.title if hasattr(chunk.retrieved_context, 'title') else None,
                                    'text': chunk.retrieved_context.text if hasattr(chunk.retrieved_context, 'text') else None
                                }
                            if chunk_data:  # Only add if we have data
                                grounding_metadata['grounding_chunks'].append(chunk_data)
                    
                    # Check if grounding_supports exists and is not None
                    if hasattr(candidate.grounding_metadata, 'grounding_supports') and candidate.grounding_metadata.grounding_supports:
                        grounding_metadata['grounding_supports'] = []
                        for support in candidate.grounding_metadata.grounding_supports:
                            support_data = {}
                            if hasattr(support, 'segment') and support.segment:
                                support_data['segment'] = {
                                    'start_index': support.segment.start_index if hasattr(support.segment, 'start_index') else None,
                                    'end_index': support.segment.end_index if hasattr(support.segment, 'end_index') else None,
                                    'text': support.segment.text if hasattr(support.segment, 'text') else None
                                }
                            if hasattr(support, 'grounding_chunk_indices') and support.grounding_chunk_indices:
                                support_data['grounding_chunk_indices'] = list(support.grounding_chunk_indices)
                            if hasattr(support, 'confidence_scores') and support.confidence_scores:
                                support_data['confidence_scores'] = list(support.confidence_scores)
                            if support_data:  # Only add if we have data
                                grounding_metadata['grounding_supports'].append(support_data)
            
            print(f"Grounding metadata extracted: {grounding_metadata is not None}")
            
            return {
                "success": True,
                "response": response.text,
                "grounding_metadata": grounding_metadata,
                "model": "gemini-2.5-flash"
            }
        
        except Exception as e:
            error_str = str(e)
            print(f"Query error (attempt {attempt + 1}/{max_retries}): {error_str}")
            
            # Check if it's a 503 error (model overloaded)
            if "503" in error_str or "UNAVAILABLE" in error_str or "overloaded" in error_str.lower():
                if attempt < max_retries - 1:  # Don't sleep on last attempt
                    print(f"Model overloaded, retrying in {retry_delay} seconds...")
                    import asyncio
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                    continue
                else:
                    raise HTTPException(
                        status_code=503, 
                        detail="The AI model is currently overloaded. Please try again in a few moments."
                    )
            else:
                # For other errors, print traceback and fail immediately
                print(traceback.format_exc())
                raise HTTPException(status_code=500, detail=f"Query failed: {error_str}")
    
    # Should never reach here, but just in case
    raise HTTPException(status_code=500, detail="Query failed after multiple retries")


@app.get("/api/documents/{store_id}")
async def list_documents(store_id: str):
    """List documents in a File Search store"""
    try:
        store_name = f"fileSearchStores/{store_id}" if not store_id.startswith("fileSearchStores/") else store_id
        documents = []
        
        # Note: The API might not have a direct list documents method
        # This is a placeholder - adjust based on actual API capabilities
        return {
            "success": True,
            "documents": documents,
            "message": "Document listing may require additional API methods"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {str(e)}")


# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
