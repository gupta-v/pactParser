import os
from pypdf import PdfReader
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from dotenv import load_dotenv

from app.models import ExtractedContractData

# --- Configuration ---

# Load environment variables from .env file
load_dotenv(dotenv_path=".env") 

# Get the API key
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not found in .env file. Please add it.")


# --- 1. PDF Reading Logic ---

def read_pdf_text(file_path: str) -> str:
    """
    Reads a PDF file and extracts its text content page by page.
    """
    try:
        reader = PdfReader(file_path)
        full_text = ""
        for page in reader.pages:
            full_text += page.extract_text() + "\n\n--- END OF PAGE ---\n\n"
        
        if not full_text.strip():
            raise ValueError("PDF is empty or text extraction failed.")
            
        return full_text
    except Exception as e:
        print(f"Error reading PDF {file_path}: {e}")
        raise ValueError(f"Could not read PDF: {e}")

# --- 2. LangChain Parsing Logic ---

def get_extraction_chain():
    """
    Initializes the LangChain extraction chain using ChatGroq.
    """
    # Initialize the LLM
    llm = ChatGroq(
        api_key=GROQ_API_KEY,
        model="llama-3.3-70b-versatile",
        temperature=0  # Set to 0 for deterministic JSON output
    )
    
    # Get the Pydantic JSON schema
    parser = JsonOutputParser(pydantic_object=ExtractedContractData)
    json_schema = parser.get_format_instructions()
    
    # Define the prompt template
    prompt_template = """
    You are an expert legal and financial analyst AI. Your task is to
    parse the provided contract text and extract critical information.
    
    Respond *only* with a valid JSON object that strictly adheres
    to the following JSON schema. Do not add any explanatory text
    
    Enter `null` where you cannot get any information
    
    Don't make up or guess any information. 
    
    The Schema is provided try to extract and fill the needed information as many as possible 
    fill it even it feels incomplete
    
    we will score the contract on our backend 
    
    JSON Schema:
    {schema}
    
    Contract Text:
    ---
    {contract_text}
    ---
    """
    
    prompt = ChatPromptTemplate.from_template(
        prompt_template,
        partial_variables={"schema": json_schema}
    )
    
    # Create the chain: Prompt -> LLM -> JSON Parser
    chain = prompt | llm | parser
    return chain

def parse_contract_text(text: str) -> dict:
    """
    Parses the full text of a contract using the LangChain extraction chain.
    
    NOTE: For very large contracts (50MB+), the text may exceed the
    LLM's context window. A more complex "Map-Reduce" or "Refine"
    strategy would be needed. For this assignment, we'll assume
    the extracted text fits in a single prompt.
    """
    try:
        print("Initializing LLM extraction chain...")
        chain = get_extraction_chain()
        print("Calling Groq LLM to parse contract... This may take a moment.")
        
        # Invoke the chain with the contract text
        result_json = chain.invoke({"contract_text": text})
        
        print("LLM parsing complete.")
        return result_json
        
    except Exception as e:
        print(f"Error during LLM parsing: {e}")
        raise Exception(f"Failed to parse text with LLM: {e}")