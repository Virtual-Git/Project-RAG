from dotenv import load_dotenv
import os
from glob import glob


from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.tools import tool
from langchain_core.messages import HumanMessage, ToolMessage 

from langchain_community.document_loaders import UnstructuredMarkdownLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import embeddings
from langchain_chroma import Chroma

# --- Load Environment Variables and Paths ---
load_dotenv()
API = os.getenv('Gemini_API_key')
dir = '__A\\Data\\Books'

# <--- CHANGED: Renamed 'path' to 'file_paths' for clarity
file_paths = glob(os.path.join(dir, '*.md'))


if not API:
    raise ValueError("Gemini_API_key not found in environment variables.")

# <--- CHANGED: Check 'file_paths' (the list)
if not file_paths:
    # <--- CHANGED: More accurate error message
    raise ValueError(f"No .md files found in directory: {dir}") 

# --- Document Loading (FIXED) ---
print(f"Loading documents from {dir}...")
documents = [] # <--- ADDED: Initialize an empty list to hold all docs
for file_path in file_paths: # <--- ADDED: Loop through each found file path
    print(f"  -> Loading {os.path.basename(file_path)}...")
    loader = UnstructuredMarkdownLoader(file_path=file_path) # <--- CHANGED: Load one file at a time
    documents.extend(loader.load()) # <--- CHANGED: Use .extend() to add the file's content

# <--- CHANGED: Updated print message
print(f"Loaded {len(documents)} document(s) from {len(file_paths)} file(s).")

# --- Initialize the LLM ---
llm = ChatGoogleGenerativeAI(
    model='gemini-2.0-flash', # <--- KEPT AS REQUESTED
    temperature=0.7,
    google_api_key=API
)

# --- Initialize Embeddings ---
emb = embeddings.GoogleGenerativeAIEmbeddings(
    model="embedding-001",
    google_api_key=API
)
print("Embedding model loaded successfully.")

# --- Text Splitting ---
print('Chunking document...')
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
)
texts = text_splitter.split_documents(documents)
print(f"Document split into {len(texts)} chunks.")

# --- Create Chroma Vector Store ---
print("Creating Chroma vector store...")
# <--- CHANGED: The variable 'dir' was being overwritten, changed this to 'db_dir'
db_dir = '__A\\ChromaDB' 

if not os.path.exists(db_dir):
    print("Creating directory for ChromaDB...")
    os.makedirs(db_dir)

try:
    vector_store = Chroma.from_documents(
        documents=texts,
        embedding=emb,
        persist_directory=db_dir, # <--- CHANGED: Use 'db_dir'
        collection_name="my_book_collection" # <--- CHANGED: More generic name
    )
    print("Chroma vector store created successfully.")
except Exception as e:
    print(f"Error creating Chroma vector store: {e}")
    # vector_store = Chroma(persist_directory=db_dir, embedding_function=emb, collection_name="my_book_collection")
    # print("Loaded existing Chroma vector store.")


# --- Creating a Retriever ---
retriever = vector_store.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 5} 
)

# --- Define the Tool ---
@tool
def retrieve_similar_chunks(query: str) -> list[str]:
    # <--- CHANGED: Updated docstring to be generic
    """Retrieve similar chunks from the loaded documents based on the query."""
    print(f"--- Tool: Retrieving chunks for query: '{query}' ---")
    results = retriever.invoke(query)

    if not results:
        return ["No similar chunks found."] 
    return [doc.page_content for doc in results]


# --- Bind Tools to LLM ---
tools = [retrieve_similar_chunks]
llm_with_tools = llm.bind_tools(tools)

# ==================================================================
# --- START: Completed Program Loop ---
# ==================================================================

print("\nSetup complete! 🤖")
# <--- CHANGED: Generic greeting
print("You can now ask questions about your books.")
print("Type 'stop' at any time to end the conversation.")

# Store the conversation history
messages = []

while True:
    # 1. Get user input
    query = input("\nYou: ")

    # 2. Check for stop command
    if query.lower() == 'stop':
        # <--- CHANGED: Generic bot name
        print("🤖 Book Bot: Goodbye! Happy reading.")
        break

    # 3. Add user message to history
    human_msg = HumanMessage(content=query)
    messages.append(human_msg)

    try:
        # 4. Call the LLM with tools
        ai_response = llm_with_tools.invoke(messages)

        # 5. Add AI response to history
        messages.append(ai_response)

        # 6. Check if the AI wants to call a tool
        if ai_response.tool_calls:
            # <--- CHANGED: Generic bot name
            print("🤖 Book Bot: Hmm, let me check the library...")
            tool_outputs = []
            
            # 7. Execute all tool calls
            for tool_call in ai_response.tool_calls:
                if tool_call['name'] == 'retrieve_similar_chunks':
                    output = retrieve_similar_chunks.invoke(tool_call['args'])
                    
                    tool_msg = ToolMessage(
                        content=str(output),
                        tool_call_id=tool_call['id']
                    )
                    tool_outputs.append(tool_msg)
            
            # 8. Add tool outputs to history
            messages.extend(tool_outputs)

            # 9. Call the LLM *again* with the tool results
            final_answer = llm_with_tools.invoke(messages)
            
            # 10. Add final answer to history and print
            messages.append(final_answer)
            # <--- CHANGED: Generic bot name
            print(f"🤖 Book Bot: {final_answer.content}")
        
        else:
            # 6b. No tool call, LLM answered directly
            # <--- CHANGED: Generic bot name
            print(f"🤖 Book Bot: {ai_response.content}")

    except Exception as e:
        print(f"An error occurred: {e}")
        if messages:
            messages.pop()