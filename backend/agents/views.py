from rest_framework.views import APIView
from rest_framework.response import Response
from .roc_tool import fetch_roc_data           # Agent 1 (The Collector)
from .agent_2_validator import validate_and_extract  # Agent 2 (The Analyst)
from .models import Company, CompanyRawData

class CompanyResearchView(APIView):
    def post(self, request):
        # 1. Get User Inputs
        company_name = request.data.get('company_name')
        requirements = request.data.get('requirements')
        
        if not company_name or not requirements:
            return Response({"error": "Missing company_name or requirements"}, status=400)

        # ====================================================
        # PHASE 1: Agent 1 (Scrape the Web)
        # ====================================================
        print(f"🔎 Agent 1: Searching for '{company_name}'...")
        agent_1_response = fetch_roc_data(company_name, requirements)
        
        # If Agent 1 failed or found nothing, stop here
        if agent_1_response.get("status") != "success":
            return Response({
                "status": "error", 
                "message": "Agent 1 failed to find data.", 
                "details": agent_1_response
            })

        # ====================================================
        # PHASE 2: Store Evidence (The Audit Trail)
        # ====================================================
        # Ensure the Parent Company exists in DB
        company_obj, _ = Company.objects.get_or_create(name=company_name)
        
        raw_texts_for_ai = [] # This list will be sent to Agent 2
        raw_entries = agent_1_response.get("data", [])
        
        print(f"💾 Saving {len(raw_entries)} raw sources to Database...")
        
        for entry in raw_entries:
            # A. Collect text for Agent 2 to read immediately
            raw_texts_for_ai.append(entry['raw_text'])
            
            # B. Save to Database (Evidence Locker)
            CompanyRawData.objects.create(
                company=company_obj,
                user_prompt=requirements,
                source_domain=entry['source_domain'],
                source_url=entry['source_url'],
                raw_text=entry['raw_text'] # We save the full messy text
            )

        # ====================================================
        # PHASE 3: Agent 2 (Validate & Extract)
        # ====================================================
        print(f"🤖 Agent 2: Analyzing text to answer '{requirements}'...")
        
        # Pass the list of text strings to the AI
        final_insight = validate_and_extract(requirements, raw_texts_for_ai)
        
        # (Optional) Update the main Company table with the new findings?
        # If Agent 2 found a specific field like 'CEO', you could update company_obj here.
        # For now, we just return it to the user.

        return Response({
            "status": "success",
            "pipeline": "Scrape -> DB Save -> AI Validate",
            "company": company_name,
            "sources_processed": len(raw_entries),
            "final_answer": final_insight  # <--- Clean, validated JSON
        })