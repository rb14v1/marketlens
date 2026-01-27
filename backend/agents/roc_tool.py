<<<<<<< HEAD
import requests
import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import trafilatura  # Ensure you have 'pip install trafilatura'

def fetch_roc_data(company_name, user_requirements):
    """
    Agent 1 (Deep Scraper - Scalable Version): 
    1. Searches for links.
    2. VISITS up to 10 top links.
    3. Returns data + list of sources.
    """
    print(f"🔎 Agent 1: Deep searching for {company_name} | Need: {user_requirements}...")
    
    # 1. Construct Query
    search_query = f"{company_name} {user_requirements} list text"
    
    url = "https://html.duckduckgo.com/html/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    data = {'q': search_query}
    
    collected_data = []
    visited_sources_list = [] # <--- NEW: Track domains for UI

    try:
        # --- PHASE 1: SEARCH ---
        response = requests.post(url, data=data, headers=headers)
        if response.status_code != 200:
            return {"status": "error", "message": "Search blocked"}

        soup = BeautifulSoup(response.text, 'html.parser')
        results = soup.find_all('div', class_='result')
        
        # --- PHASE 2: VISIT & SCRAPE (Limit increased to 10) ---
        target_count = 10 
        success_count = 0
        
        for res in results: 
            if success_count >= target_count: break 

            link_tag = res.find('a', class_='result__a')
            if not link_tag: continue
            
            target_url = link_tag.get('href')
            domain = urlparse(target_url).netloc
            
            # Skip noise
            if "facebook.com" in domain or "instagram.com" in domain:
                continue

            print(f"   👉 Visiting: {domain}...")
            
            try:
                # 1. Download the Full Page
                downloaded = trafilatura.fetch_url(target_url)
                
                # 2. Extract the Main Text
                if downloaded:
                    full_text = trafilatura.extract(downloaded)
                else:
                    full_text = None

                if full_text and len(full_text) > 100:
                    collected_data.append({
                        "source_domain": domain,
                        "source_url": target_url,
                        "raw_text": full_text
                    })
                    visited_sources_list.append(domain) # Add to clean list
                    success_count += 1
                else:
                    print(f"      ⚠️ Skipped {domain} (No readable text)")

            except Exception as e:
                print(f"      ❌ Error visiting {domain}")
                continue

        return {
            "status": "success",
            "company_name": company_name,
            "data": collected_data,
            "source_list": visited_sources_list # <--- Returns list for UI
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}
=======
import re
from urllib.parse import urlparse
from ddgs import DDGS
import trafilatura
# 🟢 Import your new specific tool
from .logo_tool import get_company_logo 

# ==============================================================================
# 🕵️‍♂️ AGENT 1: MULTI-QUERY SEARCHER + EXTERNAL LOGO TOOL
# ==============================================================================
def fetch_roc_data(company_name, user_requirements):
    yield {"type": "log", "message": f"Agent 1: Analyzing requirements for {company_name}..."}
    
    # 🟢 STEP 1: GENERATE SMART QUERIES
    # Split user input by newlines or commas to separate distinct topics
    raw_topics = [t.strip() for t in re.split(r'[\n,]', user_requirements) if t.strip()]
    
    # Always start with a Broad Official Search
    search_queries = [f'"{company_name}" official corporate profile overview facts']
    
    # Add specific queries for each user requirement (Limit to top 3 to keep speed high)
    for topic in raw_topics[:3]:
        # Clean up the topic to make it a better keyword (remove "how many", "what is")
        clean_topic = re.sub(r'\b(what is|how many|give me|tell me about)\b', '', topic, flags=re.IGNORECASE).strip()
        if len(clean_topic) > 2:
            search_queries.append(f'"{company_name}" {clean_topic}')
            
    # Deduplicate queries
    search_queries = list(set(search_queries))
    
    collected_data = []
    visited_sources_list = []
    visited_domains = set()
    official_domain = None
    
    BLOCKED_DOMAINS = [
        "facebook.com", "instagram.com", "twitter.com", "youtube.com", "tiktok.com",
        "reddit.com", "quora.com", "glassdoor.com", "medium.com"
    ]

    try:
        # 🟢 STEP 2: RUN MULTIPLE SEARCHES
        for query in search_queries:
            print(f"DEBUG: DDGS Search for: {query}")
            yield {"type": "log", "message": f"Searching: {query}..."}
            
            # Use fewer results per query (e.g. 4) since we run multiple queries
            results = list(DDGS().text(query, region="wt-wt", max_results=4))
            
            if not results: continue

            # --- PROCESS RESULTS ---
            target_count_per_query = 3
            success_count = 0
            
            for res in results: 
                if success_count >= target_count_per_query: break 
                
                target_url = res.get('href')
                if not target_url: continue
                
                domain = urlparse(target_url).netloc.lower()
                
                # Global Deduplication
                if domain in visited_domains or any(x in domain for x in BLOCKED_DOMAINS): continue
                
                # 🟢 IDENTIFY OFFICIAL DOMAIN (For Logo Tool)
                # If we see a result that isn't Wikipedia/LinkedIn, it's likely the company site
                if not official_domain and not any(x in domain for x in ["wikipedia", "linkedin", "bloomberg", "reuters"]):
                    official_domain = target_url

                yield {"type": "log", "message": f"Visiting: {domain}..."}
                
                try:
                    downloaded = trafilatura.fetch_url(target_url)
                    
                    if downloaded:
                        # 2. Extract Text
                        full_text = trafilatura.extract(downloaded)

                        if full_text and len(full_text) > 300:
                            if "please login" in full_text.lower(): continue
                                
                            collected_data.append({
                                "source_domain": domain,
                                "source_url": target_url,
                                "raw_text": full_text[:15000]
                            })
                            visited_sources_list.append(domain)
                            visited_domains.add(domain)
                            success_count += 1
                    
                except Exception: continue

        # 🟢 FINAL STEP: Use the dedicated Logo Tool
        # We pass the 'official_domain' we found (e.g., version1.com) to get the best logo
        final_logo = get_company_logo(company_name, official_domain)
        
        if final_logo:
            print(f"DEBUG: Logo found via API: {final_logo}")
        else:
            print("DEBUG: No logo found.")

        if not collected_data:
             yield {"type": "result", "payload": {"status": "error", "message": "No valid data found after multiple searches."}}
             return

        yield {"type": "result", "payload": {
            "status": "success",
            "company_name": company_name,
            "data": collected_data,
            "source_list": visited_sources_list,
            "logo": final_logo 
        }}

    except Exception as e:
        print(f"CRITICAL AGENT 1 ERROR: {e}")
        yield {"type": "result", "payload": {"status": "error", "message": str(e)}}
>>>>>>> final_version
