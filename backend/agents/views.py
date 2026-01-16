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
        # PHASE 1: Agent 1 (Scrape the Web - Upgraded)
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
        
        # Capture the list of websites for the UI (New Feature)
        scraped_sites_list = agent_1_response.get("source_list", [])
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

        # ====================================================
        # PHASE 4: Agent 3 (Competitive Comparison - OPTIONAL)
        # ====================================================
        enable_comparison = request.data.get('enable_comparison', False)
        competitor_names_str = request.data.get('competitor_names', "")
        comparison_result = None

        if enable_comparison and competitor_names_str:
            competitors = [c.strip() for c in competitor_names_str.split(',') if c.strip()]
            competitor_data_list = []
            
            from .agent_3_comparison import compare_companies # Lazy import

            print(f"⚖️ Agent 3 Triggered: Comparing against {competitors}...")

            for comp in competitors:
                print(f"   🔎 Agent 1 (Re-tasked): Searching for competitor '{comp}'...")
                # Reuse Agent 1 to get competitor data
                comp_response = fetch_roc_data(comp, requirements) # We use same requirements
                
                if comp_response.get("status") == "success":
                    # Extract raw text from the best source found for this competitor
                    # For simplicity in this agent system, we take the top 2-3 sources text
                    comp_raw_texts = [entry['raw_text'] for entry in comp_response.get("data", [])[:3]]
                    competitor_data_list.append({
                        "name": comp,
                        "data": "\n".join(comp_raw_texts)
                    })
            
            if competitor_data_list:
                comparison_result = compare_companies(company_name, final_insight, competitor_data_list)

        return Response({
            "status": "success",
            "company": company_name,
            "scraped_sources": scraped_sites_list, 
            "total_sources": len(scraped_sites_list),
            "final_answer": final_insight,
            "comparison": comparison_result # <--- NEW: Comparison Data
        })