# rag_agent.py
# A simple RAG (Retrieval-Augmented Generation) agent for the grocery data.
# It embeds a small knowledge base with Vertex AI, stores the vectors in
# ChromaDB, retrieves the most relevant facts for a question, and asks
# Gemini to answer using only those facts.

from google import genai
from google.cloud import bigquery
import chromadb

PROJECT = "retail-pipeline-499301"
LOCATION = "us-central1"
EMBED_MODEL = "gemini-embedding-001"   # Vertex AI embedding model
CHAT_MODEL = "gemini-2.5-flash"        # Vertex AI chat model

# Connect to Vertex AI (uses keyless gcloud login — no key file).
client = genai.Client(vertexai=True, project=PROJECT, location=LOCATION)

# Connect to BigQuery (same keyless gcloud login).
bq = bigquery.Client(project=PROJECT)


def embed(text):
    """Turn a piece of text into a vector (list of numbers) using Vertex AI."""
    result = client.models.embed_content(model=EMBED_MODEL, contents=text)
    return result.embeddings[0].values


# 1. The knowledge base: pulled LIVE from BigQuery 
def load_facts_from_bigquery():
    """Query BigQuery and turn each department's totals into a fact sentence."""
    print("Fetching the latest sales numbers from BigQuery...")
    query = """
        SELECT department, ROUND(SUM(total_sales), 2) AS total
        FROM `retail-pipeline-499301.retail.dept_daily_sales`
        GROUP BY department
        ORDER BY total DESC
    """
    rows = list(bq.query(query).result())

    # Identify the top and bottom seller so the facts include rankings.
    top = rows[0]
    bottom = rows[-1]

    facts = []
    for row in rows:
        line = f"The {row['department']} department has about ${row['total']:.2f} in total sales"
        if row['department'] == top['department']:
            line += " — the highest of all departments."
        elif row['department'] == bottom['department']:
            line += " — the lowest of all departments."
        else:
            line += "."
        facts.append(line)

    # A few static, business-context facts that aren't in the table.
    facts += [
        "The dairy department sells milk, yogurt, cheese, butter, and eggs.",
        "The bakery department sells sourdough, bagels, croissants, and whole wheat bread.",
        "The pantry department sells olive oil, pasta, marinara sauce, rice, and beans.",
        "Daily sales are summarized by department in a BigQuery table called dept_daily_sales.",
    ]
    return facts


knowledge_base = load_facts_from_bigquery()
print(f"Loaded {len(knowledge_base)} facts from BigQuery.\n")

# 2. Set up ChromaDB (a local vector store) 
chroma = chromadb.Client()
collection = chroma.get_or_create_collection(name="grocery_kb")

# 3. Embed every fact and store it in the vector store
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


#4. Try a couple of example questions
for q in ["Which department sells the most?", "What does the dairy department sell?"]:
    print(f"Q: {q}")
    print(f"A: {answer(q)}\n")

#5. Now ask your own questions
print("Ask your own questions (type 'quit' to exit):")
while True:
    user_q = input("You: ")
    if user_q.strip().lower() in ("quit", "exit", ""):
        print("Goodbye!")
        break
    print(f"A: {answer(user_q)}\n")
