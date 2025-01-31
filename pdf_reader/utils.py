# pdfprocessor/utils.py
import os
from langchain_community.document_loaders import PyMuPDFLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_groq import ChatGroq
from langchain.chains import RetrievalQA

def process_pdf(pdf_path, vector_db_path):
    # Load document
    loader = PyMuPDFLoader(pdf_path)
    documents = loader.load()

    # Split text
    text_splitter = CharacterTextSplitter(
        chunk_size=2000,
        chunk_overlap=400
    )
    texts = text_splitter.split_documents(documents)

    # Create embeddings
    embeddings = HuggingFaceEmbeddings()

    # Create vector DB
    vectordb = Chroma.from_documents(
        documents=texts,
        embedding=embeddings,
        persist_directory=vector_db_path
    )
    vectordb.persist()
    
    return vectordb

def create_qa_chain(vector_db_path):
    # Initialize Groq LLM
    llm = ChatGroq(
        api_key=os.getenv("GROQ_API_KEY"),
        model_name="llama3-70b-8192",
        temperature=0
    )

    # Load vector DB
    embeddings = HuggingFaceEmbeddings()
    vectordb = Chroma(
        persist_directory=vector_db_path,
        embedding_function=embeddings
    )

    return RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vectordb.as_retriever(),
        return_source_documents=True
    )