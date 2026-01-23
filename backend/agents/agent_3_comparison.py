import os
import json
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()
client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2024-02-15-preview"
)

def compare_companies(primary_company, primary_data, competitor_data_list):
    """
    Agent 3: Competitive Comparison.
    Dynamically builds the table structure to ensure ALL competitors are included.
    """
    print(f"Agent 3: Comparing {primary_company} against {len(competitor_data_list)} competitors...")

    # 1. Prepare Data Context
    competitor_context = ""
    competitor_names = []
    
    for comp in competitor_data_list:
        name = comp['name']
        competitor_names.append(name)
        competitor_context += f"\n<<< DATA FOR COMPETITOR: {name} >>>\n{comp.get('data', 'No data available')}\n"

    # 2. 🟢 DYNAMIC JSON EXAMPLE GENERATOR
    # This forces the AI to output columns for exactly the competitors we found.
    example_row = f'{{ "category": "Strengths", "{primary_company}": "• Item 1", '
    for name in competitor_names:
        example_row += f'"{name}": "• Strength A", '
    example_row = example_row.rstrip(", ") + " }"

    prompt = f"""
    You are a Senior Market Strategy Consultant (Agent 3).
    
    TASK: Perform a SWOT comparison between {primary_company} and its competitors: {", ".join(competitor_names)}.
    
    CRITICAL RULES:
    1. **NO CONTAMINATION**: When filling a competitor's column, ONLY use data from that competitor's section below. Do NOT copy {primary_company}'s data.
    2. **ALL COLUMNS**: The output table MUST have a column for "{primary_company}" and columns for: {", ".join(competitor_names)}.
    3. **STRICT SWOT**: Generate exactly 4 rows: "Strengths", "Weaknesses", "Opportunities", "Threats".
    4. **FORMAT**: Use bullet points (•). Keep them concise.
    5. **MISSING DATA**: If data is missing for a specific cell, write "N/A".
    
    PRIMARY COMPANY DATA ({primary_company}):
    {json.dumps(primary_data, indent=2)}
    
    COMPETITOR RAW DATA:
    {competitor_context}
    
    OUTPUT JSON FORMAT (Strictly follow this structure):
    {{
        "swot_table": [
            {example_row},
            {{ "category": "Weaknesses", ... (same columns) }},
            {{ "category": "Opportunities", ... (same columns) }},
            {{ "category": "Threats", ... (same columns) }}
        ],
        "market_position_summary": "A 2-sentence summary comparing these companies."
    }}
    """

    try:
        response = client.chat.completions.create(
            model=os.getenv("AZURE_DEPLOYMENT_NAME"),
            messages=[
                {"role": "system", "content": "You are a helpful API that outputs only JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)

    except Exception as e:
        print(f"Agent 3 Error: {e}")
        return {"error": str(e)}