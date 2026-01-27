from rest_framework.views import APIView
<<<<<<< HEAD
from rest_framework.response import Response
from .roc_tool import fetch_roc_data           # Agent 1 (The Collector)
from .agent_2_validator import validate_and_extract  # Agent 2 (The Analyst)
from .models import Company, CompanyRawData
=======
from django.http import StreamingHttpResponse
from .roc_tool import fetch_roc_data           # Agent 1 (The Collector)
from .agent_2_validator import validate_and_extract    # Agent 2 (The Analyst)
from .models import Company, CompanyRawData
import json
import concurrent.futures  # 🟢 REQUIRED FOR FAST PARALLEL SEARCH
>>>>>>> final_version

class CompanyResearchView(APIView):
    def post(self, request):
        # 1. Get User Inputs
<<<<<<< HEAD
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
        
        return Response({
            "status": "success",
            "company": company_name,
            "scraped_sources": scraped_sites_list, # <--- NEW: List of websites for UI
            "total_sources": len(scraped_sites_list),
            "final_answer": final_insight  # <--- Clean, validated JSON
        })
=======
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
                for event in fetch_roc_data(company_name, requirements):
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
                # 🟢 PHASE 4: OPTIMIZED PARALLEL COMPARISON
                # ====================================================
                comparison_result = None
                competitors = []
                
                if enable_comparison:
                    if competitor_names_str:
                        competitors = [c.strip() for c in competitor_names_str.split(',') if c.strip()]
                    elif final_insight and final_insight.get("extracted_data"):
                        auto_comps = final_insight["extracted_data"].get("Competitors")
                        if auto_comps and isinstance(auto_comps, list):
                            competitors = auto_comps[:3]
                            yield f"data: {json.dumps({'type': 'log', 'message': f'Auto-detected competitors: {competitors}'})}\n\n"

                if enable_comparison and competitors:
                    try:
                        from .agent_3_comparison import compare_companies
                        yield f"data: {json.dumps({'type': 'log', 'message': f'Agent 3: Analyzing {len(competitors)} competitors simultaneously...'})}\n\n"

                        competitor_data_list = []
                        clean_comp_query = "official corporate profile facts strengths weaknesses market position"

                        # 🟢 Helper function to run inside threads
                        def fetch_competitor_data(comp_name):
                            full_text = ""
                            # We iterate the generator to completion to get the final result
                            for event in fetch_roc_data(comp_name, clean_comp_query):
                                if event['type'] == 'result' and event['payload'].get("status") == "success":
                                    # Grab top 2 sources only to save time/tokens
                                    texts = [e['raw_text'] for e in event['payload'].get("data", [])[:2]]
                                    full_text = "\n".join(texts)
                            return {"name": comp_name, "data": full_text}

                        # 🟢 ThreadPoolExecutor runs searches in PARALLEL
                        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                            # Submit all tasks
                            future_to_comp = {executor.submit(fetch_competitor_data, comp): comp for comp in competitors}
                            
                            for future in concurrent.futures.as_completed(future_to_comp):
                                comp_name = future_to_comp[future]
                                try:
                                    data = future.result()
                                    if data["data"]:
                                        competitor_data_list.append(data)
                                        yield f"data: {json.dumps({'type': 'log', 'message': f'✔ Data fetched for {comp_name}'})}\n\n"
                                    else:
                                        yield f"data: {json.dumps({'type': 'log', 'message': f'⚠ No data found for {comp_name}'})}\n\n"
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
                    "logo": None # Explicitly None as requested
                }
                yield f"data: {json.dumps({'type': 'complete', 'payload': final_payload})}\n\n"
            
            except Exception as outer_e:
                import traceback
                print(f"CRITICAL STREAM ERROR: {traceback.format_exc()}")
                yield f"data: {json.dumps({'type': 'error', 'message': f'Server Error: {str(outer_e)}'})}\n\n"

        return StreamingHttpResponse(event_stream(), content_type='text/event-stream')
>>>>>>> final_version
