import requests
import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse

def fetch_roc_data(company_name, user_requirements):
    """
    Agent 1 (Deep Scraper - Safe Version): 
    Uses requests+BS4 to avoid lxml/trafilatura segfaults.
    """
    yield {"type": "log", "message": f"Agent 1: Deep searching for {company_name}..."}
    
    # 1. Construct Query
    clean_requirements = user_requirements.replace('\n', ' ').strip()
    search_query = f'"{company_name}" {clean_requirements} data'
    
    url = "https://html.duckduckgo.com/html/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Referer": "https://www.google.com/"
    }
    data = {'q': search_query}
    
    collected_data = []
    visited_sources_list = []

    try:
        # --- PHASE 1: SEARCH ---
        print(f"DEBUG: Searching {url} for {search_query}")
        response = requests.post(url, data=data, headers=headers, timeout=20)
        
        if response.status_code != 200:
            yield {"type": "result", "payload": {"status": "error", "message": f"Search blocked (Status {response.status_code})"}}
            return

        soup = BeautifulSoup(response.text, 'html.parser')
        results = soup.find_all('div', class_='result')
        
        if not results:
             yield {"type": "log", "message": "No search results found."}
             yield {"type": "result", "payload": {"status": "error", "message": "No results"}}
             return

        # --- PHASE 2: VISIT & SCRAPE (Sequential Safe) ---
        target_count = 5
        success_count = 0
        
        for res in results: 
            if success_count >= target_count: break 

            link_tag = res.find('a', class_='result__a')
            if not link_tag: continue
            
            target_url = link_tag.get('href')
            domain = urlparse(target_url).netloc
            
            # Filters
            if any(x in domain for x in ["facebook.com", "instagram.com", "youtube.com", "twitter.com"]):
                continue

            yield {"type": "log", "message": f"Visiting: {domain}..."}
            print(f"DEBUG: Visiting {target_url}")
            
            try:
                # SAFE SCRAPING
                site_resp = requests.get(target_url, headers=headers, timeout=10)
                if site_resp.status_code == 200:
                    site_soup = BeautifulSoup(site_resp.text, 'html.parser')
                    
                    # Kill script and style elements
                    for script in site_soup(["script", "style", "nav", "footer", "header"]):
                        script.extract()
                        
                    full_text = site_soup.get_text(separator=' ', strip=True)

                    if full_text and len(full_text) > 200:
                        collected_data.append({
                            "source_domain": domain,
                            "source_url": target_url,
                            "raw_text": full_text
                        })
                        visited_sources_list.append(domain)
                        success_count += 1
                        print(f"DEBUG: Scraped {domain} len={len(full_text)}")
                    else:
                        yield {"type": "log", "message": f"Skipped {domain} (Low content)"}
                else:
                    yield {"type": "log", "message": f"Skipped {domain} (Status {site_resp.status_code})"}

            except Exception as e:
                print(f"DEBUG: Error visiting {domain}: {e}")
                continue

        yield {"type": "result", "payload": {
            "status": "success",
            "company_name": company_name,
            "data": collected_data,
            "source_list": visited_sources_list
        }}

    except Exception as e:
        print(f"DEBUG: Top level error: {e}")
        yield {"type": "result", "payload": {"status": "error", "message": str(e)}}