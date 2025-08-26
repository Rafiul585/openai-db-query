from langchain.llms import OpenAI
from langchain.sql_database import SQLDatabase
from fastapi import FastAPI
from pydantic import BaseModel
import openai
import psycopg2  # To interact with PostgreSQL and get schema information

# Initialize FastAPI
app = FastAPI()


# Define the QuestionRequest model
class QuestionRequest(BaseModel):
    question: str


# OpenAI API Key (use environment variables for security in production)
openai_api_key = ""

# Database connection URI
DB_URI = "postgresql://nadeem:nadeem@192.168.70.218:5432/demo_hrms"


# Define a function to get relevant tables
def get_relevant_tables(question: str):
    """
    Preprocess the question to identify relevant tables based on keywords in the question.
    This function can be enhanced to analyze column names as well.
    """
    # Keywords related to the query. You can expand this list based on your domain.
    query_keywords = ["employee_employee"]

    relevant_tables = []

    # Connect to the database using psycopg2
    conn = psycopg2.connect(DB_URI)
    cursor = conn.cursor()

    # Get all tables from the database
    cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';")
    tables = cursor.fetchall()

    # Check if any keyword matches table name
    for table in tables:
        if any(keyword.lower() in table[0].lower() for keyword in query_keywords):
            relevant_tables.append(table[0])

    # Close the connection
    cursor.close()
    conn.close()

    return relevant_tables


# Define the /ask endpoint
@app.post("/ask")
async def ask_question(req: QuestionRequest):
    """
    Endpoint to process a user's query using the database.
    """
    # Initialize OpenAI with the API key
    llm = OpenAI(
        temperature=1,
        openai_api_key=openai_api_key
    )

    # Get relevant tables based on the question
    relevant_tables = get_relevant_tables(req.question)

    if not relevant_tables:
        return {"error": "No relevant tables found based on the query."}

    # Create schema information with the relevant tables
    schema_info = f"Relevant Tables: {', '.join(relevant_tables)}"

    # Update the prompt with the relevant table(s) information
    prompt = f"Given the relevant tables: {schema_info}, answer the following question: {req.question}. Provide the total number of employees based on the available data in the relevant tables. Only return the count of employees, no explanations or table discussions."

    # Generate SQL query using OpenAI (manually)
    chain_output = llm(prompt)

    # Return the response
    return {
        "question": req.question,
        "answer": chain_output,
        "relevant_tables": relevant_tables
    }
