import os
import glob
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename # <-- ADDED: For secure file handling

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.tools import tool
from langchain_core.messages import HumanMessage, ToolMessage
from langchain_community.document_loaders import UnstructuredMarkdownLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import embeddings
from langchain_chroma import Chroma

# --- App & RAG Component Initialization ---
app = Flask(__name__)

# --- Global Config ---
BOOK_DIRECTORY = 'PROJECT RAG\\Internal_Directory\\Data\\Books'
DB_DIR = 'PROJECT RAG\\Internal_Directory\\ChromaDB'
ALLOWED_EXTENSIONS = {'md'} # <-- ADDED: Only allow .md files

# --- Global RAG Components ---
llm = None
emb = None
retriever = None
llm_with_tools = None
file_names = []
messages = []
text_splitter = None # <-- ADDED: Make global
vector_store = None # <-- ADDED: Make global

# --- Helper Function for Upload ---
def allowed_file(filename):
    """Checks if the file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- The Retrieval Tool ---
@tool
def retrieve_similar_chunks(query: str) -> list[str]:
    """Retrieve similar chunks from the loaded documents based on the query."""
    global retriever
    if not retriever:
        return ["Error: Retriever not initialized."]
    print(f"--- Tool: Retrieving chunks for query: '{query}' ---")
    results = retriever.invoke(query)
    if not results:
        return ["No similar chunks found."]
    return [doc.page_content for doc in results]

# --- One-Time Setup Function ---
def setup_rag():
    """Loads all models, finds files, and builds the vector store."""
    # <-- ADDED: `global` for splitter and store
    global llm, emb, retriever, llm_with_tools, file_names, messages, text_splitter, vector_store
    
    print("--- Initializing RAG System ---")
    load_dotenv()
    API = os.getenv('Gemini_API_key')
    
    if not API:
        raise ValueError("Gemini_API_key not found in environment variables.")

    # 1. Find .md Files
    file_paths = glob.glob(os.path.join(BOOK_DIRECTORY, '*.md'))
    if not file_paths:
        print(f"Warning: No .md files found in directory: {BOOK_DIRECTORY}")
    
    file_names = [os.path.basename(p) for p in file_paths]
    print(f"Found files: {file_names}")

    # 2. Load LLM & Embeddings
    llm = ChatGoogleGenerativeAI(
        model='gemini-2.0-flash',
        temperature=0.7,
        google_api_key=API
    )
    emb = embeddings.GoogleGenerativeAIEmbeddings(
        model="embedding-001",
        google_api_key=API
    )
    print("LLM and Embedding models loaded.")

    # 3. Load Documents
    documents = []
    if file_paths:
        print("Loading documents...")
        for file_path in file_paths:
            loader = UnstructuredMarkdownLoader(file_path=file_path)
            documents.extend(loader.load())
        print(f"Loaded {len(documents)} document(s) from {len(file_paths)} file(s).")
    else:
        print("No documents to load.")

    # 4. Split Documents
    # <-- ADDED: Assign to global text_splitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
    )
    texts = text_splitter.split_documents(documents)
    print(f"Document split into {len(texts)} chunks.")

    # 5. Create or Load Vector Store
    print("Initializing Chroma vector store...")
    if not os.path.exists(DB_DIR):
        os.makedirs(DB_DIR)

    try:
        # Try to load existing store
        # <-- ADDED: Assign to global vector_store
        vector_store = Chroma(
            persist_directory=DB_DIR,
            embedding_function=emb,
            collection_name="my_book_collection"
        )
        if vector_store._collection.count() == 0 and not texts:
             print("Vector store is empty, no new files to add.")
        elif vector_store._collection.count() == 0 and texts:
             print("Vector store is empty, creating new.")
             raise Exception("Empty store, will recreate.")
        else:
             print("Loaded existing Chroma vector store.")
    except Exception as e:
        print(f"Loading failed ({e}). Creating new vector store...")
        if not texts:
            print("No documents to create vector store from.")
            # Create an empty store if no docs exist
            vector_store = Chroma(
                persist_directory=DB_DIR,
                embedding_function=emb,
                collection_name="my_book_collection"
            )
        else:
            # Create new one from texts
            vector_store = Chroma.from_documents(
                documents=texts,
                embedding=emb,
                persist_directory=DB_DIR,
                collection_name="my_book_collection"
            )
        print("New Chroma vector store created and persisted.")

    # 6. Create Retriever
    retriever = vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 5}
    )

    # 7. Bind tools
    tools = [retrieve_similar_chunks]
    llm_with_tools = llm.bind_tools(tools)
    
    # 8. Reset history
    messages = []
    print("--- RAG System Ready ---")


# --- Flask Routes ---

@app.route('/')
def index():
    """Serves the main HTML page and passes in the file list."""
    global file_names
    return render_template(
        'index.html', 
        project_name="Project RAG version 1", 
        files=file_names
    )

@app.route('/chat', methods=['POST'])
def chat():
    """Handles a single chat message."""
    global llm_with_tools, messages
    
    if not llm_with_tools:
        return jsonify({"error": "RAG system not initialized"}), 500

    query = request.json.get('query')
    if not query:
        return jsonify({"error": "No query provided"}), 400
    
    human_msg = HumanMessage(content=query)
    messages.append(human_msg)

    try:
        ai_response = llm_with_tools.invoke(messages)
        messages.append(ai_response) 

        bot_message_content = ""

        if ai_response.tool_calls:
            print("--- Tool Call Detected ---")
            tool_outputs = []
            
            for tool_call in ai_response.tool_calls:
                if tool_call['name'] == 'retrieve_similar_chunks':
                    output = retrieve_similar_chunks.invoke(tool_call['args'])
                    tool_msg = ToolMessage(
                        content=str(output),
                        tool_call_id=tool_call['id']
                    )
                    tool_outputs.append(tool_msg)
            
            messages.extend(tool_outputs)
            final_answer = llm_with_tools.invoke(messages)
            messages.append(final_answer)
            bot_message_content = final_answer.content
        
        else:
            bot_message_content = ai_response.content
        
        return jsonify({"response": bot_message_content})

    except Exception as e:
        print(f"An error occurred: {e}")
        if messages:
            messages.pop()
        return jsonify({"error": str(e)}), 500

@app.route('/restart', methods=['POST'])
def restart():
    """Clears the chat history."""
    global messages
    messages = []
    print("--- Chat history cleared by user ---")
    return jsonify({"status": "restarted"})


# --- NEW UPLOAD ROUTE ---
@app.route('/upload', methods=['POST'])
def upload_file():
    """Handles file upload and indexes the new file."""
    global file_names, text_splitter, vector_store
    
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    # Check if file is an allowed type (.md)
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        
        # Check for duplicates
        if filename in file_names:
            return jsonify({"error": f"File '{filename}' already exists."}), 400
            
        # Save the file
        save_path = os.path.join(BOOK_DIRECTORY, filename)
        file.save(save_path)
        
        # --- CRITICAL: Index the new file ---
        print(f"File '{filename}' saved. Indexing...")
        try:
            # 1. Load just the new file
            loader = UnstructuredMarkdownLoader(file_path=save_path)
            new_documents = loader.load()
            
            # 2. Split just the new file
            new_texts = text_splitter.split_documents(new_documents)
            print(f"Adding {len(new_texts)} new chunks to vector store.")
            
            # 3. Add new chunks to the existing vector store
            vector_store.add_documents(new_texts)
            print("Vector store updated.")
            
            # 4. Update the global file list
            file_names.append(filename)
            
            # 5. Return success
            return jsonify({
                "status": "success", 
                "filename": filename,
                "message": f"Successfully uploaded and indexed '{filename}'."
            }), 201
            
        except Exception as e:
            print(f"Error indexing new file: {e}")
            # Clean up: Remove the partially-failed upload
            os.remove(save_path)
            return jsonify({"error": f"File saved, but indexing failed: {e}"}), 500
        # --- End of indexing ---
            
    else:
        return jsonify({"error": "Invalid file type. Only .md files are allowed."}), 400
# --- END OF NEW ROUTE ---


# --- Run the App ---
if __name__ == '__main__':
    setup_rag() # Run the expensive setup once
    app.run(debug=True, port=5000)































# import os
# import glob
# from dotenv import load_dotenv
# from flask import Flask, render_template, request, jsonify

# from langchain_google_genai import ChatGoogleGenerativeAI
# from langchain.tools import tool
# from langchain_core.messages import HumanMessage, ToolMessage
# from langchain_community.document_loaders import UnstructuredMarkdownLoader
# from langchain.text_splitter import RecursiveCharacterTextSplitter
# from langchain_google_genai import embeddings
# from langchain_chroma import Chroma

# # --- App & RAG Component Initialization ---

# app = Flask(__name__)

# # --- Global RAG Components ---
# # These are loaded once when the app starts.
# llm = None
# emb = None
# retriever = None
# llm_with_tools = None
# file_names = []
# # NOTE: Storing history in a global var is simple for a v1 demo
# # but not suitable for production (shared by all users).
# messages = []

# # --- The Retrieval Tool ---
# @tool
# def retrieve_similar_chunks(query: str) -> list[str]:
#     """Retrieve similar chunks from the loaded documents based on the query."""
#     global retriever
#     if not retriever:
#         return ["Error: Retriever not initialized."]
#     print(f"--- Tool: Retrieving chunks for query: '{query}' ---")
#     results = retriever.invoke(query)
#     if not results:
#         return ["No similar chunks found."]
#     return [doc.page_content for doc in results]

# # --- One-Time Setup Function ---
# def setup_rag():
#     """Loads all models, finds files, and builds the vector store."""
#     global llm, emb, retriever, llm_with_tools, file_names, messages
    
#     print("--- Initializing RAG System ---")
#     load_dotenv()
#     API = os.getenv('Gemini_API_key')
#     book_directory = 'PROJECT RAG\\Internal_Directory\\Data\\Books'
#     db_dir = 'PROJECT RAG\\Internal_Directory\\ChromaDB'

#     if not API:
#         raise ValueError("Gemini_API_key not found in environment variables.")

#     # 1. Find .md Files
#     file_paths = glob.glob(os.path.join(book_directory, '*.md'))
#     if not file_paths:
#         raise ValueError(f"No .md files found in directory: {book_directory}")
    
#     # Store just the names (e.g., "alice.md") for the sidebar
#     file_names = [os.path.basename(p) for p in file_paths]
#     print(f"Found files: {file_names}")

#     # 2. Load LLM & Embeddings
#     llm = ChatGoogleGenerativeAI(
#         model='gemini-2.0-flash',
#         temperature=0.7,
#         google_api_key=API
#     )
#     emb = embeddings.GoogleGenerativeAIEmbeddings(
#         model="embedding-001",
#         google_api_key=API
#     )
#     print("LLM and Embedding models loaded.")

#     # 3. Load Documents
#     print("Loading documents...")
#     documents = []
#     for file_path in file_paths:
#         loader = UnstructuredMarkdownLoader(file_path=file_path)
#         documents.extend(loader.load())
#     print(f"Loaded {len(documents)} document(s) from {len(file_paths)} file(s).")

#     # 4. Split Documents
#     text_splitter = RecursiveCharacterTextSplitter(
#         chunk_size=1000,
#         chunk_overlap=200,
#     )
#     texts = text_splitter.split_documents(documents)
#     print(f"Document split into {len(texts)} chunks.")

#     # 5. Create or Load Vector Store
#     print("Initializing Chroma vector store...")
#     if not os.path.exists(db_dir):
#         os.makedirs(db_dir)

#     try:
#         # Try to load existing store
#         vector_store = Chroma(
#             persist_directory=db_dir,
#             embedding_function=emb,
#             collection_name="my_book_collection"
#         )
#         # Check if it's empty
#         if vector_store._collection.count() == 0:
#              raise Exception("Vector store is empty, will recreate.")
#         print("Loaded existing Chroma vector store.")
#     except Exception as e:
#         print(f"Loading failed ({e}). Creating new vector store...")
#         # Create new one if loading fails
#         vector_store = Chroma.from_documents(
#             documents=texts,
#             embedding=emb,
#             persist_directory=db_dir,
#             collection_name="my_book_collection"
#         )
#         print("New Chroma vector store created and persisted.")

#     # 6. Create Retriever
#     retriever = vector_store.as_retriever(
#         search_type="similarity",
#         search_kwargs={"k": 5}
#     )

#     # 7. Bind tools
#     tools = [retrieve_similar_chunks]
#     llm_with_tools = llm.bind_tools(tools)
    
#     # 8. Reset history
#     messages = []
#     print("--- RAG System Ready ---")


# # --- Flask Routes ---

# @app.route('/')
# def index():
#     """Serves the main HTML page and passes in the file list."""
#     global file_names
#     return render_template(
#         'index.html', 
#         project_name="Project RAG version 1", 
#         files=file_names
#     )

# @app.route('/chat', methods=['POST'])
# def chat():
#     """Handles a single chat message."""
#     global llm_with_tools, messages
    
#     if not llm_with_tools:
#         return jsonify({"error": "RAG system not initialized"}), 500

#     query = request.json.get('query')
#     if not query:
#         return jsonify({"error": "No query provided"}), 400
    
#     # Add user message to global history
#     human_msg = HumanMessage(content=query)
#     messages.append(human_msg)

#     try:
#         # 4. Call the LLM with tools
#         ai_response = llm_with_tools.invoke(messages)
#         messages.append(ai_response) # Add its response (tool call or final)

#         bot_message_content = ""

#         # 6. Check if the AI wants to call a tool
#         if ai_response.tool_calls:
#             print("--- Tool Call Detected ---")
#             tool_outputs = []
            
#             # 7. Execute all tool calls
#             for tool_call in ai_response.tool_calls:
#                 if tool_call['name'] == 'retrieve_similar_chunks':
#                     output = retrieve_similar_chunks.invoke(tool_call['args'])
#                     tool_msg = ToolMessage(
#                         content=str(output),
#                         tool_call_id=tool_call['id']
#                     )
#                     tool_outputs.append(tool_msg)
            
#             # 8. Add tool outputs to history
#             messages.extend(tool_outputs)

#             # 9. Call the LLM *again* with the tool results
#             final_answer = llm_with_tools.invoke(messages)
#             messages.append(final_answer)
#             bot_message_content = final_answer.content
        
#         else:
#             # 6b. No tool call, LLM answered directly
#             bot_message_content = ai_response.content
        
#         return jsonify({"response": bot_message_content})

#     except Exception as e:
#         print(f"An error occurred: {e}")
#         # Remove the last user message to avoid a loop
#         if messages:
#             messages.pop()
#         return jsonify({"error": str(e)}), 500

# @app.route('/restart', methods=['POST'])
# def restart():
#     """Clears the chat history."""
#     global messages
#     messages = []
#     print("--- Chat history cleared by user ---")
#     return jsonify({"status": "restarted"})

# # --- Run the App ---
# if __name__ == '__main__':
#     setup_rag() # Run the expensive setup once
#     app.run(debug=True, port=5000)