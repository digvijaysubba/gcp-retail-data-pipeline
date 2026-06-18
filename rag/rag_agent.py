# rag_agent.py
# A simple RAG (Retrieval-Augmented Generation) agent for the grocery data.
# It embeds a small knowledge base with Vertex AI, stores the vectors in
# ChromaDB, retrieves the most relevant facts for a question, and asks
# Gemini to answer using only those facts.

from google import genai
import chromadb

PROJECT = "retail-pipeline-499301"
LOCATION = "us-central1"
EMBED_MODEL = "gemini-embedding-001"   # Vertex AI embedding model
CHAT_MODEL = "gemini-2.5-flash"        # Vertex AI chat model

# Connect to Vertex AI (uses keyless gcloud login — no key file).
client = genai.Client(vertexai=True, project=PROJECT, location=LOCATION)


def embed(text):
    """Turn a piece of text into a vector (list of numbers) using Vertex AI."""
    result = client.models.embed_content(model=EMBED_MODEL, contents=text)
    return result.embeddings[0].values


#1. The knowledge base: facts about the grocery business
knowledge_base = [
    # Total sales per department (from the BigQuery dept_daily_sales table)
    "The meat department has about $1,032 in total sales — the highest of all departments.",
    "The household department has about $1,006 in total sales.",
    "The pantry department has about $845 in total sales.",
    "The beverages department has about $735 in total sales.",
    "The frozen department has about $693 in total sales.",
    "The snacks department has about $581 in total sales.",
    "The dairy department has about $453 in total sales.",
    "The personal care department has about $446 in total sales.",
    "The bakery department has about $429 in total sales.",
    "The produce department has about $179 in total sales — the lowest of all departments.",
    # What each department sells
    "The dairy department sells milk, yogurt, cheese, butter, and eggs.",
    "The bakery department sells sourdough, bagels, croissants, and whole wheat bread.",
    "The pantry department sells olive oil, pasta, marinara sauce, rice, and beans.",
    "The departments tracked are: produce, dairy, bakery, beverages, snacks, "
    "frozen, meat, pantry, household, and personal care.",
    "Daily sales are summarized by department in a BigQuery table called dept_daily_sales.",
]

#2. Set up ChromaDB (a local vector store)
chroma = chromadb.Client()
collection = chroma.get_or_create_collection(name="grocery_kb")

#3. Embed every fact and store it in the vector store 
print("Embedding the knowledge base (this takes a few seconds)...")
collection.add(
    ids=[f"doc{i}" for i in range(len(knowledge_base))],
    embeddings=[embed(doc) for doc in knowledge_base],
    documents=knowledge_base,
)
print("Knowledge base ready.\n")


def answer(question):
    """Retrieve the most relevant facts, then ask Gemini to answer using them."""
    # Embed the question and find the 3 closest facts.
    q_vector = embed(question)
    results = collection.query(query_embeddings=[q_vector], n_results=3)
    facts = "\n".join(results["documents"][0])

    # Ask Gemini to answer using ONLY those facts.
    prompt = (
        "You are a helpful assistant for a grocery business. "
        "Answer the question using ONLY the facts below. "
        "If the facts don't contain the answer, say you don't know.\n\n"
        f"Facts:\n{facts}\n\n"
        f"Question: {question}"
    )
    response = client.models.generate_content(model=CHAT_MODEL, contents=prompt)
    return response.text


# 4. Try a couple of example questions ---
for q in ["Which department sells the most?", "What does the dairy department sell?"]:
    print(f"Q: {q}")
    print(f"A: {answer(q)}\n")

# 5. Now ask your own questions ---
print("Ask your own questions (type 'quit' to exit):")
while True:
    user_q = input("You: ")
    if user_q.strip().lower() in ("quit", "exit", ""):
        print("Goodbye!")
        break
    print(f"A: {answer(user_q)}\n")
