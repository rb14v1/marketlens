import re
import concurrent.futures
from urllib.parse import urlparse
from ddgs import DDGS
import trafilatura
# Keep your logo tool import
from .logo_tool import get_company_logo 

# ==============================================================================
# 🚀 OPTIMIZED AGENT 1: PARALLEL DOWNLOADER + LITE MODE
# ==============================================================================

def quick_download(url):
    """
    Helper function to download a single page with a strict 3-second timeout.
    """
    try:
        # 3-second timeout forces the agent to skip slow websites immediately
        downloaded = trafilatura.fetch_url(url) # trafilatura doesn't allow easy timeout arg, so we rely on its defaults or wrap it if needed.
        # Ideally, trafilatura.fetch_url(url) is usually fast, but for stricter control:
        # downloaded = trafilatura.fetch_url(url) 
        if downloaded:
            text = trafilatura.extract(downloaded)
            if text and len(text) > 300 and "please login" not in text.lower():
                return {"url": url, "text": text[:15000], "domain": urlparse(url).netloc.lower()}
    except Exception:
        pass
    return None

def fetch_roc_data(company_name, user_requirements, lite_mode=False):
    """
    Args:
        lite_mode (bool): If True, runs only 1 query (Best for Competitors).
                          If False, runs deep search (Best for Primary Company).
    """
    yield {"type": "log", "message": f"Agent 1:{' [Lite Mode]' if lite_mode else ''} Analyzing {company_name}..."}
    
    # 🟢 STEP 1: GENERATE QUERIES
    search_queries = []
    
    if lite_mode:
        # Competitors only get 1 broad search to save time
        search_queries.append(f'"{company_name}" official corporate profile facts')
    else:
        # Primary company gets detailed search
        search_queries.append(f'"{company_name}" official corporate profile overview facts')
        raw_topics = [t.strip() for t in re.split(r'[\n,]', user_requirements) if t.strip()]
        for topic in raw_topics[:2]: # Limit to top 2 extra topics
            clean_topic = re.sub(r'\b(what is|how many|give me|tell me about)\b', '', topic, flags=re.IGNORECASE).strip()
            if len(clean_topic) > 2:
                search_queries.append(f'"{company_name}" {clean_topic}')
    
    # Deduplicate queries
    search_queries = list(set(search_queries))
    
    collected_urls = []
    visited_domains = set()
    official_domain = None
    
    BLOCKED_DOMAINS = [
        "facebook.com", "instagram.com", "twitter.com", "youtube.com", "tiktok.com",
        "reddit.com", "quora.com", "glassdoor.com", "medium.com"
    ]

    # 🟢 STEP 2: GATHER URLS (Fast Search)
    max_urls_to_scan = 3 if lite_mode else 6  # Scan fewer pages for competitors
    
    for query in search_queries:
        if len(collected_urls) >= max_urls_to_scan: break
        
        yield {"type": "log", "message": f"Searching: {query}..."}
        try:
            # Get results but don't download yet
            results = list(DDGS().text(query, region="wt-wt", max_results=max_urls_to_scan))
            
            for res in results:
                if len(collected_urls) >= max_urls_to_scan: break
                
                target_url = res.get('href')
                if not target_url: continue
                
                domain = urlparse(target_url).netloc.lower()
                
                # Filter bad domains
                if domain in visited_domains or any(x in domain for x in BLOCKED_DOMAINS): continue
                
                visited_domains.add(domain)
                collected_urls.append(target_url)
                
                # Try to snag official domain for Logo Tool
                if not official_domain and not any(x in domain for x in ["wikipedia", "linkedin", "bloomberg", "reuters"]):
                    official_domain = target_url
        except Exception as e:
            print(f"Search Error: {e}")

    # 🟢 STEP 3: PARALLEL DOWNLOAD (The Speed Boost)
    # We download ALL found URLs at the exact same time
    collected_data = []
    visited_sources_list = []
    
    if collected_urls:
        yield {"type": "log", "message": f"⚡ Parallel downloading {len(collected_urls)} pages..."}
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            # Submit all download tasks
            future_to_url = {executor.submit(quick_download, url): url for url in collected_urls}
            
            for future in concurrent.futures.as_completed(future_to_url):
                result = future.result()
                if result:
                    collected_data.append({
                        "source_domain": result['domain'],
                        "source_url": result['url'],
                        "raw_text": result['text']
                    })
                    visited_sources_list.append(result['domain'])

    # 🟢 STEP 4: LOGO (Only if not in Lite Mode, or optional)
    final_logo = None
    if not lite_mode: 
        final_logo = get_company_logo(company_name, official_domain)

    # Final Return
    if not collected_data:
        yield {"type": "result", "payload": {"status": "error", "message": "No valid data found."}}
    else:
        yield {"type": "result", "payload": {
            "status": "success",
            "company_name": company_name,
            "data": collected_data,
            "source_list": visited_sources_list,
            "logo": final_logo 
        }}