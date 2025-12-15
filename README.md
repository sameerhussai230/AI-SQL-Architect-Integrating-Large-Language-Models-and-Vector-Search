# AI SQL Architect: Integrating Large Language Models and Vector Search

![Python](https://img.shields.io/badge/Python-3.9%2B-blue) ![Streamlit](https://img.shields.io/badge/Framework-Streamlit-red) ![LLM](https://img.shields.io/badge/AI-Groq%20API%20%7C%20Vector%20Search-blue) ![License](https://img.shields.io/badge/License-MIT-yellow)

## 🚀 Project Overview

The **AI SQL Architect** project is specifically designed for **Text-to-SQL generation** using a sophisticated integration of Large Language Models (LLMs) and Vector Search technologies. This system simplifies the process of translating natural language queries into executable SQL commands, enhancing the accessibility and efficiency of database interactions. The architecture is engineered to leverage state-of-the-art AI to understand and process user inputs, thereby automating the generation of SQL queries tailored to user needs.

### 🌟 Key Capabilities
*   **Complex Query Handling:** Initially configured with the **AdventureWorks** database, the system handles simple retrievals to complex joins and aggregations.
*   **Dynamic Adaptation:** It dynamically processes new, valid questions regarding the schema and performs complex operations between multiple tables.
*   **Validation & Visualization:** The system validates SQL accuracy, rephrases results into natural language, and visualizes insights using interactive **Plotly charts**.
*   **Database Agnostic:** While optimized for AdventureWorks, the architecture is flexible and can be aligned with various complex database schemas for different organizational use cases.

---

### 🏗️ System Architecture

Below is a detailed workflow of the system, illustrating how user inputs are transformed into visual insights.

![Architectural Diagram](https://github.com/sameerhussai230/AI-SQL-Architect-Integrating-Large-Language-Models-and-Vector-Search/assets/85198601/4c624170-1bdb-40a6-a031-3891a487080d)

1.  **User Question Input:** The entry point where users input their natural language queries.
2.  **Query Question Collection:** Utilizes **Vector Search** to identify relevant previously asked questions that align with the user's input.
3.  **Query Schema Collection:** Retrieves schema information corresponding to the user's query to ensure generated SQL is contextually appropriate.
4.  **SQL & Schema Retrieval:** Extracts necessary SQL queries and schema details from the database to aid in accurate generation.
5.  **Generate Prompt:** Constructs a detailed, context-aware prompt from the retrieved information for the LLM.
6.  **LLM (Groq API):** Processes the comprehensive prompt to generate precise SQL queries.
7.  **SQL Server Execution:** Outputs and runs the SQL query tailored to the user's request.
8.  **Results & Visualization:** Manages the execution, processes the data into DataFrames, and renders **Plotly charts** via the **Streamlit** interface.
9.  **Vector DB Initialization:** Handles the one-time setup of the vector database to facilitate the querying process.

## Installation

Follow these steps to get started with the AI SQL Architect:

1. Clone the repository:
   ```bash
   git clone https://github.com/sameerhussai230/AI-SQL-Architect-Integrating-Large-Language-Models-and-Vector-Search.git
   ```
2. Navigate to the project directory:
   ```bash
   cd AI-SQL-Architect-Integrating-Large-Language-Models-and-Vector-Search
   ```
3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Initial Setup

**Vector Database Initialization**: Run the `vector.py` script a single time to initialize and populate the vector database. This setup is crucial for the project's search capabilities:

```bash
python vector.py
```

## Usage

To run the application, use the following command:

```bash
streamlit run app.py
```

This command launches the Streamlit interface in your browser where you can input queries and view SQL results along with visual data representations.

## Results
### 1) What is the total freight cost for each shipping method
![Screenshot 2024-06-23 155658](https://github.com/sameerhussai230/AI-SQL-Architect-Integrating-Large-Language-Models-and-Vector-Search/assets/85198601/a2b045c4-b98c-426a-8a48-525db9f27fee)

### 2) Who are the top 5 salespeople by total sales amount?

![Screenshot 2024-06-23 155602](https://github.com/sameerhussai230/AI-SQL-Architect-Integrating-Large-Language-Models-and-Vector-Search/assets/85198601/b30a00de-de9f-41a1-931d-5bf668f39fbc)

### 3) Give the full names of top 5 customers responsible for the highest sales?
![Screenshot 2024-06-23 162237](https://github.com/sameerhussai230/AI-SQL-Architect-Integrating-Large-Language-Models-and-Vector-Search/assets/85198601/21247363-8f6e-4cfc-bd23-d8210bf02ca1)

### 4) How is the customer base distributed across different sales territories
![Screenshot 2024-06-23 161431](https://github.com/sameerhussai230/AI-SQL-Architect-Integrating-Large-Language-Models-and-Vector-Search/assets/85198601/9d7350be-4c48-4d90-bfc4-27e6efc0e5ae)

### 5) How many sales orders are there per sales territory?
![Screenshot 2024-06-23 160939](https://github.com/sameerhussai230/AI-SQL-Architect-Integrating-Large-Language-Models-and-Vector-Search/assets/85198601/c1cc2ea7-a627-486f-8dff-e605af403005)


