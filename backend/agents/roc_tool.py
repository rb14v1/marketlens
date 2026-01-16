import requests
import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import trafilatura  # Ensure you have 'pip install trafilatura'

def fetch_roc_data(company_name, user_requirements):
    """
    Agent 1 (Deep Scraper - Scalable Version): 
    Generates events:
    - {"type": "log", "message": "..."}
    - {"type": "result", "payload": {...}}
    """
    yield {"type": "log", "message": f"🔎 Agent 1: Deep searching for {company_name} | Need: {user_requirements}..."}
    
    # 1. Construct Query
    clean_requirements = user_requirements.replace('\n', ' ').strip()
    search_query = f'"{company_name}" {clean_requirements} data'
    
    url = "https://html.duckduckgo.com/html/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    data = {'q': search_query}
    
    collected_data = []
    visited_sources_list = []

    try:
        # --- PHASE 1: SEARCH ---
        response = requests.post(url, data=data, headers=headers)
        if response.status_code != 200:
            yield {"type": "result", "payload": {"status": "error", "message": "Search blocked"}}
            return

        soup = BeautifulSoup(response.text, 'html.parser')
        results = soup.find_all('div', class_='result')
        
        # --- PHASE 2: VISIT & SCRAPE ---
        target_count = 10 
        success_count = 0
        
        for res in results: 
            if success_count >= target_count: break 

            link_tag = res.find('a', class_='result__a')
            if not link_tag: continue
            
            target_url = link_tag.get('href')
            domain = urlparse(target_url).netloc
            
            if "facebook.com" in domain or "instagram.com" in domain:
                continue

            yield {"type": "log", "message": f"👉 Visiting: {domain}..."}
            
            try:
                downloaded = trafilatura.fetch_url(target_url)
                full_text = None
                if downloaded:
                    full_text = trafilatura.extract(downloaded)

                if full_text and len(full_text) > 100:
                    collected_data.append({
                        "source_domain": domain,
                        "source_url": target_url,
                        "raw_text": full_text
                    })
                    visited_sources_list.append(domain)
                    success_count += 1
                else:
                    yield {"type": "log", "message": f"   ⚠️ Skipped {domain} (No readable text)"}

            except Exception as e:
                yield {"type": "log", "message": f"   ❌ Error visiting {domain}"}
                continue

        yield {"type": "result", "payload": {
            "status": "success",
            "company_name": company_name,
            "data": collected_data,
            "source_list": visited_sources_list
        }}

    except Exception as e:
        yield {"type": "result", "payload": {"status": "error", "message": str(e)}}