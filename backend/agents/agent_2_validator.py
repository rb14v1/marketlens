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
    
    combined_text = ""
    for idx, text in enumerate(raw_text_list):
        combined_text += f"\n--- SOURCE {idx+1} ---\n{text[:5000]}" 
    
    combined_text = combined_text[:30000]

    # 🟢 OPTIMIZED PROMPT: ALLOWS INTERNAL KNOWLEDGE FALLBACK
    prompt = f"""
    You are a Senior Market Strategy Consultant.
    
    TARGET COMPANY: "{company_name}"
    USER QUESTION: "{user_requirement}"
    
    SCRAPED WEB DATA:
    {combined_text}
    
    INSTRUCTIONS:
    1. **PRIORITY 1 (WEB DATA)**: First, try to answer the user's question using ONLY the Scraped Web Data above. This is the most trusted source.
    2. **PRIORITY 2 (INTERNAL KNOWLEDGE)**: If the answer is NOT in the web data, use your own internal training data to answer.
       - IMPORTANT: If you use internal knowledge, add "(Source: AI Knowledge Base)" to the end of the answer.
    3. **FILTER**: Ignore data belonging to other companies (e.g. ignore 'Adam Mosseri' if asking about Google).
    4. **COMPETITORS**: List 3-5 major competitors.
    5. **SUMMARY**: Write a professional executive summary about {company_name}.
    
    OUTPUT JSON FORMAT:
    {{
        "answer_found": true,
        "summary": "Executive summary...",
        "extracted_data": {{
            "Key_Answer": "The answer here",
            "Competitors": ["Comp1", "Comp2"],
            "Details": "Additional context..."
        }},
        "confidence_score": "High/Medium/Low"
    }}
    """

    try:
        response = client.chat.completions.create(
            model=os.getenv("AZURE_DEPLOYMENT_NAME"),
            messages=[
                {"role": "system", "content": "You are a helpful market analyst. Output valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3, # Slightly higher temperature to allow knowledge retrieval
            response_format={"type": "json_object"}
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
