# Project RAG v1

A full-stack web application that allows you to chat with your Markdown documents in real-time, powered by a Retrieval-Augmented Generation (RAG) pipeline.

This application provides a clean, modern chat interface where you can ask questions. The backend, built with Flask and LangChain, retrieves relevant information from your local `.md` files using a vector store (ChromaDB) and generates answers using Google's Gemini.

<br>

<img width="1286" height="618" alt="image" src="https://github.com/user-attachments/assets/7dd5feae-ee07-4d6f-8479-ba0f54f08694" />


-----

## 🚀 Core Features.

  * **Interactive Chat UI:** A clean, responsive chat interface built with Flask, HTML, CSS, and JavaScript.
  * **RAG Pipeline:** Leverages Google's Gemini (`gemini-2.0-flash`) and Google's embedding models (`embedding-001`) for intelligent, context-aware responses.
  * **Persistent Vector Storage:** Uses **ChromaDB** to create and store document embeddings, persisting them locally in the `Internal_Directory/Data/ChromaDB` directory.
  * **Dynamic Document Indexing:**
      * **Load on Startup:** Automatically finds, loads, and indexes all `.md` files from the `Internal_Directory/Data/Books` directory when the server starts.
      * **Live Upload & Indexing:** Upload new `.md` files directly from the web interface. The app indexes them *immediately* without requiring a server restart.
  * **Collapsible File Browser:** A sidebar lists all currently indexed documents.
  * **Chat History Management:** Clear the current conversation to start fresh at any time.

-----

## 🛠️ Tech Stack

  * **Backend:** Python, Flask
  * **Frontend:** HTML5, CSS3, JavaScript (Fetch API)
  * **Generative AI (LLM):** Google Gemini (`gemini-2.0-flash`) # you can change it to any google GenAI model
  * **Embeddings:** Google Generative AI Embeddings (`embedding-001`)
  * **Vector Database:** ChromaDB (local persistence)
  * **Core Python Libraries:** `langchain`, `langchain-google-genai`, `langchain-chroma`, `unstructured`, `python-dotenv`

-----

## ⚙️ Setup & Installation

Follow these steps to get the project running locally.

### 1\. Prerequisites

  * Python 3.8+
  * Access to a Google Gemini API key

### 2\. Initial Setup

1.  **Clone the Repository (or download the files):**

    ```bash
    git clone https://github.com/Virtual-Git/Project-RAG.git
    ```

2.  **Create and Activate a Virtual Environment:**

    ```bash
    # Windows
    python -m venv venv
    .\venv\Scripts\activate

    # macOS/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install Dependencies:**

    ```bash
    pip install flask langchain langchain-google-genai langchain-community langchain-chroma unstructured markdown python-dotenv werkzeug
    ```

    **OR**
    ```bash
    pip install -r requirements.txt
    ```

    *(Note: `werkzeug` is used for `secure_filename`)*

5.  **Create the Environment File:**
    Create a file named `.env` in the root of your project directory. Add your Google API key to it:

    ```ini
    Gemini_API_key=YOUR_ACTUAL_API_KEY_HERE
    ```

6.  **Create the Data Directory:**
    The application expects your Markdown files to be in `Internal_Directory/Data/Books/`.

    ```bash
    # Windows
    mkdir -p Internal_Directory\Data\Books

    # macOS/Linux
    mkdir -p Internal_Directory/Data/Books
    ```

    You can place any initial `.md` files you want in this directory. The `Internal_Directory/Data/ChromaDB` folder will be created automatically when you first run the app.

### 3\. Running the Application

1.  **Start the Flask Server:**

    ```bash
    python app.py
    ```

2.  **Access the Web Interface:**
    Open your browser and navigate to:
    **`http://127.0.0.1:5000/`**  *or* any other link shown on terminal

-----

## 📖 How to Use

1.  **Chat with your Books:** Type your questions about the loaded documents into the input box at the bottom and press "Send". The bot will use the RAG pipeline to find answers.

2.  **View Files:** The sidebar on the left shows all `.md` files that are currently indexed in the vector store. You can toggle this sidebar using the (☰) menu button.

3.  **Upload a New Book:**

      * In the sidebar, click "Choose File".
      * Select any `.md` file from your computer.
      * Click "Upload".
      * The system will save the file to the `Internal_Directory/Data/Books` directory and add its contents to the live vector store. The new file will appear in the list, and you can immediately start asking questions about it.

4.  **Clear Chat:** Click the "Clear Chat" button in the header to restart the conversation history.

-----

## 📂 Project Structure

```
.
├── Internal_Directory/
│   ├── Data/
│   │   ├── Books/          # Location for all .md files (user-provided)
│   │   └── ChromaDB/       # Persistent vector store (auto-generated)
├── static/
│   ├── css/
│   │   └── style.css       # All frontend styles
│   └── js/
│       └── main.js         # Frontend logic (chat, upload, sidebar)
├── templates/
│   └── index.html          # Main Flask/Jinja2 HTML template
├── app.py                  # The Flask backend (RAG logic, API routes)
├── .env                    # Stores API keys (MUST be kept private)
└── README.md               # You are here
```
