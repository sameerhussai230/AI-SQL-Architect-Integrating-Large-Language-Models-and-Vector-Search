import csv
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.utils import embedding_functions

# Load data from CSV file
def load_data(filename, doc_index, meta_index):
    with open(filename, newline='') as file:
        reader = csv.reader(file)
        next(reader)  # Skip the header
        documents, metadatas, ids = [], [], []
        for id, line in enumerate(reader, 1):
            if len(line) > max(doc_index, meta_index):
                documents.append(line[doc_index])
                metadatas.append({"id": line[meta_index]})
                ids.append(str(id))
            else:
                print(f"Skipping line {id} due to insufficient columns: {line}")
    return documents, metadatas, ids

# Retrieve specific column data by ID from CSV file
def retrieve_data_by_ids(filename, ids, column_index):
    with open(filename, newline='') as file:
        reader = csv.reader(file)
        header = next(reader)  # Skip the header
        data_map = {line[0]: line[column_index] for line in reader if len(line) > column_index}
    return [data_map[id] for id in ids if id in data_map]

# Initialize the vector database
def initialize_database():
    chroma_client = chromadb.PersistentClient(path="vectordb")
    sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-mpnet-base-v2")
    return chroma_client, sentence_transformer_ef

# Create a collection in the database
def create_collection(client, name, embedding_function):
    return client.get_or_create_collection(name=name, embedding_function=embedding_function)

# Add data to the vector database
def add_data_to_database(collection, documents, metadatas, ids):
    collection.add(documents=documents, metadatas=metadatas, ids=ids)

# Query the vector database for the question collection
def query_question_collection(collection, query_text):
    results = collection.query(
        query_texts=[query_text],
        n_results=2,
        include=['documents', 'distances', 'metadatas']
    )
    return [meta['id'] for meta in results['metadatas'][0]]

# Query the vector database for the schema collection
def query_schema_collection(collection, query_text):
    results = collection.query(
        query_texts=[query_text],
        n_results=2,
        include=['documents', 'distances', 'metadatas']
    )
    return [meta['id'] for meta in results['metadatas'][0]]

# Load the data
q_documents, q_metadatas, q_ids = load_data('question.csv', 1, 0)
s_documents, s_metadatas, s_ids = load_data('schema.csv', 1, 0)

# Initialize the vector database
client, embedding_function = initialize_database()

# Create and fill collections
question_collection = create_collection(client, "question_collection", embedding_function)
schema_collection = create_collection(client, "schema_collection", embedding_function)

# Add data to collections
add_data_to_database(question_collection, q_documents, q_metadatas, q_ids)
add_data_to_database(schema_collection, s_documents, s_metadatas, s_ids)
