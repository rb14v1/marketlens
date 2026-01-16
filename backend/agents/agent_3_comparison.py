import os
import json
from openai import AzureOpenAI
from dotenv import load_dotenv

# Load params
load_dotenv()
endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
api_key = os.getenv("AZURE_OPENAI_API_KEY")
deployment = os.getenv("AZURE_DEPLOYMENT_NAME")

client = AzureOpenAI(
    azure_endpoint=endpoint,
    api_key=api_key,
    api_version="2024-02-15-preview"
)

def compare_companies(primary_company, primary_data, competitor_data_list):
    """
    Agent 3: Competitive Comparison Agent.
    
    Args:
        primary_company (str): Name of primary company
        primary_data (dict): Validated data of primary company (from Agent 2)
        competitor_data_list (list): List of dicts, each containing 'name' and 'raw_text' or 'validated_data' for competitors.
    """
    print(f"⚖️ Agent 3: Comparing {primary_company} against {len(competitor_data_list)} competitors...")

    # Prepare context
    competitor_context = ""
    for comp in competitor_data_list:
        competitor_context += f"\n--- COMPETITOR: {comp['name']} ---\n{comp.get('data', 'No data available')}\n"

    prompt = f"""
    You are the Competitive Comparison Agent (Agent 3).
    
    TASK: Compare '{primary_company}' against the following competitors based on the provided data.
    
    PRIMARY COMPANY DATA:
    {json.dumps(primary_data, indent=2)}
    
    COMPETITOR DATA:
    {competitor_context}
    
    STRICT INSTRUCTIONS:
    1. **TASK**: Create a Side-by-Side SWOT Analysis Table.
    2. **TABLE STRUCTURE**:
       - The 'swot_table' MUST contain exactly 4 rows: "Strengths", "Weaknesses", "Opportunities", "Threats".
       - Columns must be: "category" (Row Name), "{primary_company}" (Primary Data), and one column for EACH competitor (e.g., "Competitor 1", "Competitor 2").
    3. **CONTENT**:
       - For each cell, provide a concise bulleted list (as a string) of the top 3 items.
       - E.g., "• Strong Brand\n• Global Reach\n• High R&D"
    4. **FORBIDDEN**: Do NOT include financial metrics like Revenue or Employee count in this table. This is purely qualitative SWOT.
    5. JSON Output ONLY. No Markdown.
    
    OUTPUT JSON FORMAT:
    {{
        "swot_table": [
            {{ "category": "Strengths", "{primary_company}": "• Item 1\n• Item 2", "Competitor_Name": "• Item A\n• Item B" }},
            {{ "category": "Weaknesses", "{primary_company}": "• Item 1", "Competitor_Name": "• Item A" }},
            {{ "category": "Opportunities", "{primary_company}": "• Item 1", "Competitor_Name": "• Item A" }},
            {{ "category": "Threats", "{primary_company}": "• Item 1", "Competitor_Name": "• Item A" }}
        ],
        "market_position_summary": "Brief narrative summary of the competitive landscape."
    }}
    """

    try:
        response = client.chat.completions.create(
            model=deployment,
            messages=[
                {"role": "system", "content": "You are a helpful API that outputs only JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)

    except Exception as e:
        print(f"❌ Agent 3 Error: {e}")
        return {"error": str(e)}
