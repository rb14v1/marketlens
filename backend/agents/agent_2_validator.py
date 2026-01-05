import os
import json
from openai import AzureOpenAI
from dotenv import load_dotenv

# 1. Load the .env file
load_dotenv()

# 2. Get keys
endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
api_key = os.getenv("AZURE_OPENAI_API_KEY")
deployment = os.getenv("AZURE_DEPLOYMENT_NAME")

# Check keys
if not api_key or not endpoint:
    print("❌ ERROR: Azure credentials not found in .env file!")

# 3. Initialize Client
client = AzureOpenAI(
    azure_endpoint=endpoint,
    api_key=api_key,
    api_version="2024-02-15-preview"
)

def validate_and_extract(user_requirement, raw_text_list):
    """
    Agent 2 (Azure): Safe for large data.
    """
    print(f"🤖 Agent 2 (Azure): Analyzing {len(raw_text_list)} sources...")
    
    # SAFEGUARD: Limit total text to 30,000 chars to avoid Azure errors
    combined_text = "\n--- NEW SOURCE ---\n".join(raw_text_list)
    if len(combined_text) > 30000:
        print("   ⚠️ Text too long! Truncating to safe limit...")
        combined_text = combined_text[:30000]

    prompt = f"""
    You are a Senior Data Analyst.
    
    TASK: Answer the user requirement based on the provided scraped data.
    USER REQUIREMENT: "{user_requirement}"
    
    SOURCE DATA (From {len(raw_text_list)} websites):
    {combined_text}
    
    INSTRUCTIONS:
    1. VALIDATE: Cross-reference the sources. Prioritize recent/official info.
    2. SUMMARIZE: Provide a clear, professional summary (2-3 sentences).
    3. ANSWER: specific to the user's requirement. If the user asks for "CEO", just provide the name. If "Revenue", just the number.
    
    JSON FORMAT:
    {{
        "answer_found": true,
        "summary": "Professional summary of the findings.",
        "extracted_data": {{
            "Key_Answer": "The direct answer to the user's question (e.g. Sundar Pichai)"
        }},
        "confidence_score": "High/Medium/Low"
    }}
    """

    try:
        response = client.chat.completions.create(
            model=deployment,  # Uses .env deployment name
            messages=[
                {"role": "system", "content": "You are a helpful API that outputs only JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)

    except Exception as e:
        print(f"❌ Azure Error: {e}")
        return {"answer_found": False, "error": str(e)}