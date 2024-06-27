import streamlit as st
from pydantic import BaseModel
import requests
import json
import logging
import pyodbc
import os
from groq import Groq
import numpy as np
import sqlparse
import pandas as pd
import plotly.express as px
from dotenv import load_dotenv
from vector import retrieve_data_by_ids, query_schema_collection, query_question_collection, question_collection, schema_collection
import re

# Load environment variables from .env file
load_dotenv()

class QueryRequest(BaseModel):
    question: str
    user_name: str

def create_prompt(question):
    queried_question_ids = query_question_collection(question_collection, question)
    queried_schema_ids = query_schema_collection(schema_collection, question)
    sql_queries = retrieve_data_by_ids('question.csv', queried_question_ids, 2)
    schemas = retrieve_data_by_ids('schema.csv', queried_schema_ids, 2)
    sql_queries_f = "\n\n".join(sql_queries)
    schema_queries_f = "\n\n".join(schemas)
    prompt = f"""
    --
    You are an expert in writing T-SQL Queries, tasked with generating SQL Server queries based on user questions about data stored in various tables in SQL Server.
    Schema Information which may be relevant:
    {schema_queries_f}
    Example SQL Query which is more relevant:
    {sql_queries_f}
    Given a user's question about this data, write a valid SQL Server query that accurately extracts or calculates the requested information from these tables and adheres to SQL best practices, optimizing for readability and performance where applicable.
    Here are some tips for writing SQL Server queries:
    - Ensure all tables referenced are from your SQL Server instance.
    - Always use aliases for tables.
    - Use built-in SQL Server functions like GETDATE() for the current date.
    - For constructing T-SQL queries related to time intervals like "this year" or "this month," use the GETDATE(), DATEADD, and DATEDIFF functions to dynamically calculate the appropriate date ranges.
    - Aggregated fields like COUNT(*) must be appropriately named.
    - When filtering by location, branch names, or department names, use the LIKE operator with percentage signs to allow partial matches. For example, use 'BranchName LIKE '%Noida%'' for branch names and 'DeptName LIKE '%Software%'' for department names.
    Question:
    {question}
    Reminder: Generate a SQL Server query to answer the question:
    - Use only those table names which are provided above in Example SQL Query and Schema Information, do not take irrelevant table names.
    - Do not apply Join Condition unnecessarily between the tables.
    - Respond as a valid JSON Document.
    - [Best] If the question can be answered with the available tables: {{"sql": "<sql here>"}}
    - If the question cannot be answered with the available tables: {{"error": "<explanation here>"}}
    - Ensure that the entire output is returned on only one single line.
    - Keep your query as simple and straightforward as possible; do not use subqueries.
    """
    return prompt

def create_plotly_chart_prompt(sql_query, question, schema_info):
    prompt = f"""
    --
    Schema Information which may be relevant:
    {schema_info}

    Given the following SQL query:
    {sql_query}

    Generate Python code to create a Plotly chart that visualizes the data. The chart should be relevant to the user's question:
    Question: {question}
    The code should:
    - Assume the data is already loaded into a DataFrame named 'results_df'
    - Create a Plotly chart that is relevant to the data and the question
    - Display the chart using Streamlit's st.plotly_chart
    - Respond with only the Python code, and no additional text or comments
    """
    return prompt

def create_reflection_prompt_for_plotly(question, error_message):
    return f"""
    --
    There was an error while generating the Plotly chart code. The following error was encountered:
    {error_message}
    Please regenerate the Python code to create a Plotly chart that visualizes the data related to the question:
    Question: {question}
    The code should:
    - Assume the data is already loaded into a DataFrame named 'results_df'
    - Create a Plotly chart that is relevant to the data and the question
    - Display the chart using Streamlit's st.plotly_chart
    - Respond with only the Python code, and no additional text or comments
    - Ensure no syntax errors like the one previously encountered occur.
    """

def chat_with_groq(client, prompt, model):
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0,
    )
    return completion.choices[0].message.content

def get_json_output(llm_response):
    llm_response_no_escape = llm_response.replace('\\n', ' ').replace('\n', ' ').replace('\\', '').strip()
    try:
        open_idx = llm_response_no_escape.index('{')
        close_idx = llm_response_no_escape.rindex('}') + 1
        cleaned_result = llm_response_no_escape[open_idx:close_idx]
        json_result = json.loads(cleaned_result)
        if 'sql' in json_result:
            query = json_result['sql']
            return True, sqlparse.format(query, reindent=True, keyword_case='upper')
        elif 'error' in json_result:
            return False, json_result['error']
    except (ValueError, json.JSONDecodeError):
        return False, "No valid JSON content found in response."
    return False, "Response format is incorrect or unexpected."

def execute_sql_query(query):
    server = ""
    database = ""
    conn_str = (
        f"Driver={{SQL Server}};"
        f"Server={server};"
        f"Database={database};"
        f"Trusted_Connection=yes;"
    )
    try:
        conn = pyodbc.connect(conn_str)
        df = pd.read_sql(query, conn)
        return df, None
    except Exception as e:
        error_message = str(e)
        print(f"Failed to execute query: {error_message}")
        return pd.DataFrame(), error_message
    finally:
        if conn:
            conn.close()

def get_reflection(client, full_prompt, error_message, model):
    reflection_prompt = f"""
    You were given the following prompt:
    {full_prompt}
    This was the error encountered:
    {error_message}
    There was an error with the response, either in the query itself.
    Ensure that the following rules are satisfied when correcting your response:
    1. SQL is valid Transact-SQL, given the provided metadata and the Transact-SQL querying rules
    2. The query SPECIFICALLY references the correct tables:'SalesOrderHeader', 'SalesOrderDetail', 'Customer', 'Product', 'Person' and those tables are properly aliased? (this is the most likely cause of failure)
    3. Response is in the correct format ({{"sql": "<sql_here>"}} or {{"error": "<explanation here>"}}) with no additional text?
    4. All fields are appropriately named
    5. There are no unnecessary sub-queries
    6. ALL TABLES are aliased (extremely important) 
    Rewrite the response and respond ONLY with the valid output format with no additional commentary.
    """
    return chat_with_groq(client, reflection_prompt, model)

def get_summarization(client, user_question, df, model, additional_context):
    prompt = f'''
    A user asked the following question pertaining to local database tables:
    {user_question}
    To answer the question, a dataframe was returned:
    Dataframe:
    {df}
    In a few sentences, summarize the data in the table as it pertains to the original user question. Avoid qualifiers like "based on the data" and do not comment on the structure or metadata of the table itself.
    '''
    if additional_context != '':
        prompt += f'''
        The user has provided this additional context:
        {additional_context}
        '''
    return chat_with_groq(client, prompt, model)

def extract_python_code(response_text):
    match = re.search(r"```python(.*?)```", response_text, re.DOTALL)
    if match:
        return match.group(1).strip()
    else:
        return response_text.strip()

def execute_plotly_code(plotly_code, df):
    # Remove Markdown backticks if present
    cleaned_code = plotly_code.replace('```', '').strip()

    # Full Python code including necessary imports and DataFrame assignment
    full_code = f"""
import pandas as pd
import plotly.express as px
import streamlit as st

# Assigning the DataFrame from the function argument
results_df = df

# Plotly code to be executed
{cleaned_code}
"""

    # Define the execution environment
    exec_env = {
        'px': px,        # Ensure Plotly express is available
        'st': st,        # Ensure Streamlit is available
        'pd': pd,        # Ensure Pandas is available
        'df': df,        # Passing the DataFrame directly
        'results_df': df # Making the DataFrame available as 'results_df'
    }

    try:
        # Execute the Python code within the defined environment
        exec(full_code, exec_env)
    except SyntaxError as e:
        st.error(f"SyntaxError in generated code: {e}")
        st.code(full_code, language='python')  # Display the problematic code for better debugging
    except Exception as e:
        st.error(f"Error in executing Plotly code: {e}")
        st.code(full_code, language='python')  # Display the problematic code for better debugging


def main():
    # Configure page to use the full screen width
    st.set_page_config(layout="wide")
    st.title("Ask Your Database")
    user_question = st.text_input("Enter your question:")
    additional_context = "summarize the above info"
    if st.button("Analyze"):
        if user_question:
            # Initialize the progress bar
            progress_bar = st.progress(0)
            # Setup and authenticate with Groq API
            groq_api_key = os.getenv("GROQ_API_KEY")
            client = Groq(api_key=groq_api_key, base_url=os.getenv("GROQ_BASE_URL"))
            model = "llama3-70b-8192"
            progress_bar.progress(10)  # Update progress after setup

            # Generate the SQL query prompt and process the response
            full_prompt = create_prompt(user_question)
            progress_bar.progress(20)  # Update progress after generating prompt
            llm_response = chat_with_groq(client, full_prompt, model)
            progress_bar.progress(30)  # Update progress after getting initial response

            # Initialize columns for layout, evenly split
            col1, col2 = st.columns(2)  # Two equal columns
            valid_sql_response = False
            max_retries = 3
            attempts = 0

            while not valid_sql_response and attempts < max_retries:
                is_sql, result = get_json_output(llm_response)
                progress_bar.progress(40 + 10 * attempts)

                if is_sql:
                    results_df, error = execute_sql_query(result)
                    progress_bar.progress(60 + 10 * attempts)

                    if not results_df.empty:
                        valid_sql_response = True
                        schema_info = '\n\n'.join(retrieve_data_by_ids('schema.csv', query_schema_collection(schema_collection, user_question), 2))
                        with col1:
                            st.markdown("```sql\n" + result + "\n```")
                            summarization = get_summarization(client, user_question, results_df, model, additional_context)
                            st.write(summarization.replace('$','\\$'))
                            st.dataframe(results_df)

                        plotly_attempts = 0
                        while plotly_attempts < max_retries:
                            plotly_prompt = create_plotly_chart_prompt(result, user_question, schema_info)
                            plotly_response = chat_with_groq(client, plotly_prompt, model)
                            plotly_code = extract_python_code(plotly_response)

                            try:
                                with col2:
                                    execute_plotly_code(plotly_code, results_df)
                                break  # Successful Plotly execution
                            except Exception as e:
                                plotly_attempts += 1
                                print(f"Plotly chart attempt {plotly_attempts} of {max_retries}. Error: {str(e)}")
                                if plotly_attempts < max_retries:
                                    plotly_response = create_reflection_prompt_for_plotly(user_question, str(e))
                                    plotly_response = chat_with_groq(client, plotly_response, model)
                                else:
                                    st.error("Failed to generate valid Plotly code after multiple attempts.")

                        progress_bar.progress(100)  # Complete the progress bar
                        break  # Exit SQL loop if valid response processed
                    else:
                        error_message = f"SQL Execution Error: {error}"
                        print(error_message)
                        if attempts < max_retries - 1:
                            llm_response = get_reflection(client, full_prompt, error, model)

                else:
                    print("Invalid SQL response. Attempting reflection.")
                    if attempts < max_retries - 1:
                        llm_response = get_reflection(client, full_prompt, result, model)
                attempts += 1

            if not valid_sql_response:
                st.error("Failed to generate a valid SQL response after multiple attempts.")
                progress_bar.empty()

        else:
            st.error("Please enter your question.")
            progress_bar.empty()

if __name__ == "__main__":
    main()
