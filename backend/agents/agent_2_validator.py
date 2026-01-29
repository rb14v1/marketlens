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

def validate_and_extract(company_name, user_requirement, raw_text_list):
    """
    Agent 2 (Azure): Context-Aware Validator + Knowledge Fallback.
    """
    yield {"type": "log", "message": f"Agent 2: Verifying data specifically for '{company_name}'..."}
    
    # ⚡ SPEED OPTIMIZATION: Reduced from 30,000 -> 8,000 chars
    # This keeps the agent fast (under 30s) while still having enough data.
    combined_text = ""
    for idx, text in enumerate(raw_text_list):
        if len(combined_text) > 8000: break
        # Limit each source to 2,500 chars (focus on the top/important parts)
        combined_text += f"\n--- SOURCE {idx+1} ---\n{text[:2500]}" 
    
    combined_text = combined_text[:8000]

    # 🟢 PROMPT: STRICT MODE + SILENT COMPETITORS
    prompt = f"""
    You are a Senior Market Strategy Consultant.
    
    TARGET COMPANY: "{company_name}"
    USER QUESTION: "{user_requirement}"
    
    SCRAPED WEB DATA:
    {combined_text}
    
    INSTRUCTIONS:
    1. **VISIBLE DATA ('extracted_data')**: 
       - Extract ONLY the specific data points requested in 'USER QUESTION'.
       - 🚫 Do NOT add "Revenue", "Headquarters", or "Competitors" here unless the user explicitly asked for them.
       - Create a separate JSON key for each topic (e.g., "CEO", "Salary").
    
    2. **HIDDEN DATA ('competitors_list')**: 
       - ✅ ALWAYS identify 3 major competitors and put them in this separate list.
       - This allows the backend to run comparisons even if the user didn't ask to see the list.
    
    3. **SUMMARY**: Write a 2-sentence professional executive summary.
    
    OUTPUT JSON FORMAT:
    {{
        "answer_found": true,
        "summary": "Executive summary...",
        "extracted_data": {{
            "Requested_Item_1": "Value",
            "Requested_Item_2": "Value"
        }},
        "competitors_list": ["Comp1", "Comp2", "Comp3"], 
        "confidence_score": "High"
    }}
    """

    try:
        response = client.chat.completions.create(
            model=os.getenv("AZURE_DEPLOYMENT_NAME"),
            messages=[
                {"role": "system", "content": "You are a helpful market analyst. Output valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0, # Zero temp for strictness
            response_format={"type": "json_object"},
            timeout=30 # Safety timeout
        )
        
        result = json.loads(response.choices[0].message.content)
        
        if result.get("answer_found"):
            yield {"type": "log", "message": f"✅ Agent 2: Validated info for {company_name}."}
        else:
            yield {"type": "log", "message": f"⚠️ Agent 2: Limited data found for {company_name}."}
            
        yield {"type": "result", "payload": result}

    except Exception as e:
        yield {"type": "log", "message": f"Validation Error: {e}"}
        yield {"type": "result", "payload": {"answer_found": False, "error": str(e)}}