from google import genai
from google.genai import types

# 1. Initialize the client for Vertex AI mode
# To use your $25 credits, you MUST provide your Project ID
client = genai.Client(
    vertexai=True, 
    api_key="AQ.Ab8RN6J02bBr8NIcgiTcxaNh0lC6G_n7mAI2cLCkJbIwaY_QMA",
)

# 2. The grounding tool syntax remains the same in the new SDK
grounding_tool = types.Tool(
    google_search=types.GoogleSearch()
)

config = types.GenerateContentConfig(
    tools=[grounding_tool]
)

# 3. Call the model
# Note: Ensure the model name matches what is available in your Vertex Model Garden
response = client.models.generate_content(
    model="gemini-3.1-pro-preview", 
    contents="What is the latest ESG score of 'Prinova USA'?",
    config=config,
)

print(response.text)