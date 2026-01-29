from rest_framework.views import APIView
from django.http import StreamingHttpResponse

from .roc_tool import fetch_roc_data           # Agent 1
from .agent_2_validator import validate_and_extract    # Agent 2
from .models import Company, CompanyRawData
import json
import concurrent.futures

class CompanyResearchView(APIView):
    def post(self, request):
        # 1. Get User Inputs
        try:
            data = request.data
            if not data and request.body:
                 data = json.loads(request.body)
            
            company_name = data.get('company_name')
            requirements = data.get('requirements')
            enable_comparison = data.get('enable_comparison', False)
            competitor_names_str = data.get('competitor_names', "")
        except Exception as e:
             print(f"Request Parsing Error: {e}")
             company_name = None

        if not company_name or not requirements:
            return StreamingHttpResponse(
                iter([f"data: {json.dumps({'type': 'error', 'message': 'Missing dictionary inputs'})}\n\n"]),
                content_type='text/event-stream'
            )

        def event_stream():
            try:
                # ====================================================
                # PHASE 1: Agent 1 (Scrape Primary Company)
                # ====================================================
                agent_1_response = None
                # Run standard deep search for the main company
                for event in fetch_roc_data(company_name, requirements, lite_mode=False):
                    if event['type'] == 'log':
                         yield f"data: {json.dumps(event)}\n\n"
                    elif event['type'] == 'result':
                         agent_1_response = event['payload']
                
                if not agent_1_response or agent_1_response.get("status") != "success":
                    error_msg = agent_1_response.get('message', 'Agent 1 failed.') if agent_1_response else 'Agent 1 failed.'
                    yield f"data: {json.dumps({'type': 'error', 'message': error_msg})}\n\n"
                    return

                # ====================================================
                # PHASE 2: Store Evidence
                # ====================================================
                yield f"data: {json.dumps({'type': 'log', 'message': 'Saving sources...'})}\n\n"
                try:
                    company_obj, _ = Company.objects.get_or_create(name=company_name)
                    for entry in agent_1_response.get("data", []):
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
                # PHASE 3: Agent 2 (Validate Primary Company)
                # ====================================================
                final_insight = None
                raw_texts = [e['raw_text'] for e in agent_1_response.get("data", [])]
                
                for event in validate_and_extract(company_name, requirements, raw_texts):
                    if event['type'] == 'log':
                        yield f"data: {json.dumps(event)}\n\n"
                    elif event['type'] == 'result':
                        final_insight = event['payload']

                # ====================================================
                # 🟢 PHASE 4: TURBO PARALLEL COMPARISON
                # ====================================================
                comparison_result = None
                competitors = []
                
                if enable_comparison:
                    if competitor_names_str:
                        competitors = [c.strip() for c in competitor_names_str.split(',') if c.strip()]
                    elif final_insight:
                        # 🟢 CRITICAL FIX: Look in the new HIDDEN field first, then fallback to extracted
                        # This ensures the comparison runs even if Agent 2 is in "Strict Mode"
                        auto_comps = final_insight.get("competitors_list") or final_insight.get("extracted_data", {}).get("Competitors")
                        
                        if auto_comps and isinstance(auto_comps, list):
                            # ⚡ SPEED LIMIT: Top 2 Competitors Only
                            competitors = auto_comps[:2]
                            yield f"data: {json.dumps({'type': 'log', 'message': f'Auto-detected top 2 competitors: {competitors}'})}\n\n"
                    
                    # Safety check: Force max 2 if manual input was long
                    competitors = competitors[:2]

                if enable_comparison and competitors:
                    try:
                        from .agent_3_comparison import compare_companies
                        yield f"data: {json.dumps({'type': 'log', 'message': f'Agent 3: Quick-scanning {len(competitors)} competitors...'})}\n\n"

                        competitor_data_list = []

                        # 🟢 Helper function: FETCH 2 SOURCES (Better Quality)
                        def fetch_competitor_fast(comp_name):
                            collected_texts = []
                            # We still use lite_mode=True (searches 3 pages max)
                            # But now we collect the top 2 valid texts instead of just 1
                            for event in fetch_roc_data(comp_name, "official profile facts", lite_mode=True):
                                if event['type'] == 'result' and event['payload'].get("status") == "success":
                                    data_items = event['payload'].get("data", [])
                                    # Grab up to 2 sources
                                    for item in data_items[:2]: 
                                        collected_texts.append(item['raw_text'])
                                    break # Stop generator after getting the batch
                            
                            # Combine them so Agent 3 has more context to work with
                            full_text = "\n\n".join(collected_texts)[:20000] 
                            return {"name": comp_name, "data": full_text}

                        # 🟢 ThreadPoolExecutor: Run 2-3 searches at once
                        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                            future_to_comp = {executor.submit(fetch_competitor_fast, comp): comp for comp in competitors}
                            
                            for future in concurrent.futures.as_completed(future_to_comp):
                                comp_name = future_to_comp[future]
                                try:
                                    data = future.result()
                                    if data["data"]:
                                        competitor_data_list.append(data)
                                        yield f"data: {json.dumps({'type': 'log', 'message': f'✔ Data found for {comp_name}'})}\n\n"
                                    else:
                                        yield f"data: {json.dumps({'type': 'log', 'message': f'⚠ No data for {comp_name}'})}\n\n"
                                except Exception as exc:
                                    yield f"data: {json.dumps({'type': 'log', 'message': f'Error searching {comp_name}: {exc}'})}\n\n"

                        if competitor_data_list:
                             comparison_result = compare_companies(company_name, final_insight, competitor_data_list)
                    
                    except Exception as e:
                        import traceback
                        print(f"Agent 3 Error: {traceback.format_exc()}")
                        yield f"data: {json.dumps({'type': 'log', 'message': f'Agent 3 Error: {str(e)}'})}\n\n"

                # ====================================================
                # PHASE 5: FINAL RESPONSE
                # ====================================================
                yield f"data: {json.dumps({'type': 'log', 'message': 'Finalizing...'})}\n\n"

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
                    "logo": agent_1_response.get("logo") # Restore Logo if available
                }
                yield f"data: {json.dumps({'type': 'complete', 'payload': final_payload})}\n\n"
            
            except Exception as outer_e:
                import traceback
                print(f"CRITICAL STREAM ERROR: {traceback.format_exc()}")
                yield f"data: {json.dumps({'type': 'error', 'message': f'Server Error: {str(outer_e)}'})}\n\n"

        return StreamingHttpResponse(event_stream(), content_type='text/event-stream')