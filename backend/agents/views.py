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
            data = request.data
            # Fallback for manual JSON body parsing if DRF didn't parse it
            if not data and request.body:
                 data = json.loads(request.body)
            
            company_name = data.get('company_name')
            requirements = data.get('requirements')
            enable_comparison = data.get('enable_comparison', False)
            competitor_names_str = data.get('competitor_names', "")
        except Exception as e:
             # Fallback if parsing fails
             print(f"Request Parsing Error: {e}")
             company_name = None

        if not company_name or not requirements:
            return StreamingHttpResponse(
                iter([f"data: {json.dumps({'type': 'error', 'message': 'Missing dictionary inputs (company_name, requirements)'})}\n\n"]),
                content_type='text/event-stream'
            )

        def event_stream():
            try:
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
                    error_msg = agent_1_response.get('message', 'Agent 1 failed (No data found).') if agent_1_response else 'Agent 1 failed (No response).'
                    yield f"data: {json.dumps({'type': 'error', 'message': error_msg})}\n\n"
                    return

                # ====================================================
                # PHASE 2: Store Evidence
                # ====================================================
                yield f"data: {json.dumps({'type': 'log', 'message': 'Saving sources to Database...'})}\n\n"
                
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
                     yield f"data: {json.dumps({'type': 'log', 'message': f'DB Error: {str(e)}'})}\n\n"

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
                
                # Auto-detect competitors if missing
                competitors = []
                if enable_comparison:
                    if competitor_names_str:
                        competitors = [c.strip() for c in competitor_names_str.split(',') if c.strip()]
                    elif final_insight and final_insight.get("extracted_data"):
                        # Try to find competitors in Agent 2 extraction
                        auto_comps = final_insight["extracted_data"].get("Competitors")
                        if auto_comps and isinstance(auto_comps, list):
                            competitors = auto_comps[:3] # Limit to top 3
                            yield f"data: {json.dumps({'type': 'log', 'message': f'Auto-detected competitors: {competitors}'})}\n\n"

                if enable_comparison and competitors:
                    from .agent_3_comparison import compare_companies
                    
                    yield f"data: {json.dumps({'type': 'log', 'message': f'Agent 3: Comparing against {competitors}...'})}\n\n"

                    competitor_data_list = []
                    for comp in competitors:
                        yield f"data: {json.dumps({'type': 'log', 'message': f'Searching for competitor: {comp}...'})}\n\n"
                        
                        comp_response = None
                        for event in fetch_roc_data(comp, requirements):
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
                yield f"data: {json.dumps({'type': 'log', 'message': 'Report generation complete. Finalizing...'})}\n\n"

                # Prepare detailed sources for frontend (with URLs)
                sources_formatted = []
                if agent_1_response and "data" in agent_1_response:
                    seen_urls = set()
                    for item in agent_1_response["data"]:
                        if item["source_url"] not in seen_urls:
                            sources_formatted.append({
                                "title": item["source_domain"],
                                "url": item["source_url"]
                            })
                            seen_urls.add(item["source_url"])

                final_payload = {
                    "status": "success",
                    "company": company_name,
                    "scraped_sources": sources_formatted, 
                    "total_sources": len(sources_formatted),
                    "final_answer": final_insight,
                    "comparison": comparison_result,
                    "logo": agent_1_response.get("logo")
                }
                # Send as a special 'complete' event
                yield f"data: {json.dumps({'type': 'complete', 'payload': final_payload})}\n\n"
            
            except Exception as outer_e:
                import traceback
                print(f"CRITICAL STREAM ERROR: {traceback.format_exc()}")
                yield f"data: {json.dumps({'type': 'error', 'message': f'Server Error: {str(outer_e)}'})}\n\n"

        return StreamingHttpResponse(event_stream(), content_type='text/event-stream')