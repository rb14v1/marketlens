from rest_framework.views import APIView
from django.http import StreamingHttpResponse
from .roc_tool import fetch_roc_data           # Agent 1 (The Collector)
from .agent_2_validator import validate_and_extract  # Agent 2 (The Analyst)
from .models import Company, CompanyRawData
import json

class CompanyResearchView(APIView):
    def post(self, request):
        # 1. Get User Inputs
        try:
            # When using StreamingHttpResponse, request.data might be consumed if not careful, 
            # but for DRF APIView it's fine.
            company_name = request.data.get('company_name')
            requirements = request.data.get('requirements')
            enable_comparison = request.data.get('enable_comparison', False)
            competitor_names_str = request.data.get('competitor_names', "")
        except Exception:
             # Fallback if parsing fails
             company_name = None

        if not company_name or not requirements:
            return StreamingHttpResponse(
                iter([f"data: {json.dumps({'status': 'error', 'message': 'Missing inputs'})}\n\n"]),
                content_type='text/event-stream'
            )

        def event_stream():
            # ====================================================
            # PHASE 1: Agent 1 (Scrape the Web)
            # ====================================================
            agent_1_response = None
            for event in fetch_roc_data(company_name, requirements):
                if event['type'] == 'log':
                     yield f"data: {json.dumps(event)}\n\n"
                elif event['type'] == 'result':
                     agent_1_response = event['payload']
            
            # Check success
            if not agent_1_response or agent_1_response.get("status") != "success":
                yield f"data: {json.dumps({'type': 'error', 'message': 'Agent 1 failed.'})}\n\n"
                return

            # ====================================================
            # PHASE 2: Store Evidence
            # ====================================================
            yield f"data: {json.dumps({'type': 'log', 'message': '💾 Saving sources to Database...'})}\n\n"
            
            try:
                company_obj, _ = Company.objects.get_or_create(name=company_name)
                scraped_sites_list = agent_1_response.get("source_list", [])
                raw_entries = agent_1_response.get("data", [])
                raw_texts_for_ai = []

                for entry in raw_entries:
                    raw_texts_for_ai.append(entry['raw_text'])
                    CompanyRawData.objects.create(
                        company=company_obj,
                        user_prompt=requirements,
                        source_domain=entry['source_domain'],
                        source_url=entry['source_url'],
                        raw_text=entry['raw_text']
                    )
            except Exception as e:
                 yield f"data: {json.dumps({'type': 'log', 'message': f'⚠️ DB Error: {str(e)}'})}\n\n"

            # ====================================================
            # PHASE 3: Agent 2 (Validate & Extract)
            # ====================================================
            final_insight = None
            for event in validate_and_extract(requirements, raw_texts_for_ai):
                if event['type'] == 'log':
                    yield f"data: {json.dumps(event)}\n\n"
                elif event['type'] == 'result':
                    final_insight = event['payload']

            # ====================================================
            # PHASE 4: Agent 3 (Comparison)
            # ====================================================
            comparison_result = None
            if enable_comparison and competitor_names_str:
                competitors = [c.strip() for c in competitor_names_str.split(',') if c.strip()]
                
                from .agent_3_comparison import compare_companies
                
                yield f"data: {json.dumps({'type': 'log', 'message': f'⚖️ Agent 3: Comparing against {competitors}...'})}\n\n"

                competitor_data_list = []
                for comp in competitors:
                    yield f"data: {json.dumps({'type': 'log', 'message': f'   🔎 Searching for competitor: {comp}...'})}\n\n"
                    
                    # Call Agent 1 for competitor (Simulate blocking call since we didn't refactor recursive calls fully yet, 
                    # OR simply iterate it if we want logs from it too. Let's iterate!)
                    comp_response = None
                    for event in fetch_roc_data(comp, requirements):
                        # We can choose to stream these sub-logs or suppress them. Let's stream them.
                         if event['type'] == 'log':
                             yield f"data: {json.dumps(event)}\n\n"
                         elif event['type'] == 'result':
                             comp_response = event['payload']

                    if comp_response and comp_response.get("status") == "success":
                        comp_raw_texts = [entry['raw_text'] for entry in comp_response.get("data", [])[:3]]
                        competitor_data_list.append({
                            "name": comp,
                            "data": "\n".join(comp_raw_texts)
                        })

                if competitor_data_list:
                     comparison_result = compare_companies(company_name, final_insight, competitor_data_list)

            # ====================================================
            # PHASE 5: FINAL RESPONSE
            # ====================================================
            final_payload = {
                "status": "success",
                "company": company_name,
                "scraped_sources": scraped_sites_list, 
                "total_sources": len(scraped_sites_list),
                "final_answer": final_insight,
                "comparison": comparison_result
            }
            # Send as a special 'complete' event
            yield f"data: {json.dumps({'type': 'complete', 'payload': final_payload})}\n\n"

        return StreamingHttpResponse(event_stream(), content_type='text/event-stream')