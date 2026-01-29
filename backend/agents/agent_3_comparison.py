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
    🚀 FIXED AGENT 3: No Duplicates + Faster
    """
    print(f"Agent 3: Comparing {primary_company} against {len(competitor_data_list)} competitors...")

    competitor_context = ""
    competitor_names = []
    
    for comp in competitor_data_list:
        name = comp['name']
        competitor_names.append(name)
        
        # ⚡ SPEED FIX: Reduced to 6,000 characters.
        # This is the "Sweet Spot" - fast enough for 30s response, detailed enough for a table.
        raw_data = comp.get('data', 'No data available')[:6000]
        
        competitor_context += f"\n<<< DATA FOR COMPETITOR: {name} >>>\n{raw_data}\n"

        
    # Pre-build the structure to guide the AI
    example_row = f'{{ "category": "Strengths", "{primary_company}": "• Point 1\\n• Point 2", '
    for name in competitor_names:
        example_row += f'"{name}": "• Point A\\n• Point B", '
    example_row = example_row.rstrip(", ") + " }"

    prompt = f"""
    You are a Senior Strategy Consultant.
    
    TASK: Create a SWOT comparison table for: {primary_company} vs {", ".join(competitor_names)}.
    
    CRITICAL FORMATTING RULES:
    1. **NO DUPLICATE ROWS**: You must output EXACTLY 4 rows: "Strengths", "Weaknesses", "Opportunities", "Threats".
    2. **MERGE DATA**: If you have multiple points for "Strengths", combine them into ONE cell using line breaks (\\n) or bullet points. DO NOT create a second "Strengths" row.
    3. **CONCISE & FAST**: Keep bullet points impactful but under 15 words.
    4. **JSON ONLY**: Output valid JSON.
    
    PRIMARY COMPANY DATA:
    {json.dumps(primary_data, indent=2)[:4000]} 
    
    COMPETITOR DATA:
    {competitor_context}
    
    OUTPUT JSON FORMAT:
    {{
        "swot_table": [
            {example_row},
            {{ "category": "Weaknesses", ... }},
            {{ "category": "Opportunities", ... }},
            {{ "category": "Threats", ... }}
        ],
        "market_position_summary": "2-sentence summary of the market landscape."
    }}
    """

    try:
        response = client.chat.completions.create(
            model=os.getenv("AZURE_DEPLOYMENT_NAME"),
            messages=[
                {"role": "system", "content": "You are a helpful API. Output JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1, # Lower temperature reduces "hallucinating" extra rows
            response_format={"type": "json_object"},
            timeout=35 
        )
        return json.loads(response.choices[0].message.content)

    except Exception as e:
        print(f"Agent 3 Error: {e}")
        return {
            "swot_table": [],
            "market_position_summary": f"Comparison failed due to error: {str(e)}"
        }