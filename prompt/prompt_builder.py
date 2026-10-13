from prompt.schema_rules import ORIGINAL_SCHEMA_RULES
# prompt/prompt_builder.py
import os
from rag.fewshot_retriever import retrieve_fewshots

connection_string = os.environ.get('CONNECTION_STRING')

def build_prompt(user_query, rag_result):
    """
    GPT sẽ chỉ output Python code, bao gồm SQL query.
    Luôn wrap code trong ```python ... ```
    """
    fewshots = retrieve_fewshots(user_query)
    table_info = ""
    for t in rag_result['tables']:
        table_info += f"\nTable: {t}\n"
        if t in rag_result['columns']:
            table_info += f"Columns: {rag_result['columns'][t]}\n"

    prompt = f"""
        You are a data engineer assistant.

        Task:
        - Generate Python code that queries the database based on the user query.
        - Only return Python code inside a markdown code block like this:
        ```python
        # Your code here
        Connection string (use psycopg2): {connection_string}

        Available tables and columns:
        {table_info}

        User question:
        {user_query}

        Requirements:
        {ORIGINAL_SCHEMA_RULES}

        - Use Python and psycopg2
        - Return results in a structured format (list of dicts or pandas dataframe)
        - Only use the tables provided
        - Do not include explanations, only code in the markdown block
        - Return results in a variable named 'result' (pandas dataframe or list of dicts)
        - Only output Python code inside ```python ... ```
        - Do not expose the connection string to the output code. Express it by the environment variable "CONNECTION_STRING".

        Examples:
        Here are the examples of the related task you could check on: {fewshots}
        """
    
    return prompt