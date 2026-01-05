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