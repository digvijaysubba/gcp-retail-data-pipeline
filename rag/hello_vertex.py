# hello_vertex.py
# A tiny test that confirms  code can reach Gemini on Vertex AI
# using the keyless login (ADC)  set up with gcloud.

from google import genai

# Connects to Vertex AI in this project.
# No key needed — it automatically uses gcloud login.
client = genai.Client(
    vertexai=True,
    project="retail-pipeline-499301",
    location="us-central1",
)

# Ask Gemini a simple question.
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="In one short sentence, say hello and confirm you're Gemini running on Vertex AI.",
)

print(response.text)
