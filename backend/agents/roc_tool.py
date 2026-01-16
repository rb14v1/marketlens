import requests
import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from duckduckgo_search import DDGS
# Reload to pick up new library version

# ==============================================================================
# HELPER: Logo Extraction
# ==============================================================================
def extract_company_logo(html: str, base_url: str) -> str | None:
    if not html:
        return None
 
    soup = BeautifulSoup(html, "html.parser")
 
    # 1️⃣ Header / Navbar logos
    for img in soup.find_all("img"):
        src = img.get("src") or img.get("data-src")
        alt = (img.get("alt") or "").lower()
        cls = " ".join(img.get("class", [])).lower()
 
        if not src:
            continue
 
        text = f"{src} {alt} {cls}".lower()
 
        if any(k in text for k in ["logo", "brand", "navbar", "header"]):
            if not any(x in src.lower() for x in ["icon", "svg", "sprite"]):
                return urljoin(base_url, src)
 
    # 2️⃣ OpenGraph image (very reliable)
    og = soup.find("meta", property="og:image")
    if og and og.get("content"):
        return urljoin(base_url, og["content"])
 
    # 3️⃣ Favicon fallback
    icon = soup.find("link", rel=lambda x: x and "icon" in x.lower())
    if icon and icon.get("href"):
        return urljoin(base_url, icon["href"])
 
    return None

def fetch_roc_data(company_name, user_requirements):
    """
    Agent 1 (Deep Scraper - Safe Version): 
    Uses duckduckgo-search for search (resilient to blocks) 
    and requests+BS4 for scraping (to avoid lxml/trafilatura segfaults).
    """
    yield {"type": "log", "message": f"Agent 1: Deep searching for {company_name}..."}
    
    # 1. Construct Query
    clean_requirements = user_requirements.replace('\n', ' ').strip()
    search_query = f'"{company_name}" {clean_requirements} data'
    
    collected_data = []
    visited_sources_list = []
    found_logo = None

    try:
        # --- PHASE 1: SEARCH (Using DDGS Library) ---
        print(f"DEBUG: DDGS Search for: {search_query}")
        
        # Use DDGS context manager or direct call. Direct call is simpler.
        results_gen = DDGS().text(search_query, max_results=5)
        results = list(results_gen)
        
        if not results:
             yield {"type": "log", "message": "No search results found via API."}
             yield {"type": "result", "payload": {"status": "error", "message": "No results found"}}
             return

        # --- PHASE 2: VISIT & SCRAPE (Sequential Safe) ---
        target_count = 5
        success_count = 0
        
        # Headers for scraping (mimic browser)
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Referer": "https://www.google.com/"
        }
        
        for res in results: 
            if success_count >= target_count: break 
            
            target_url = res.get('href')
            if not target_url: continue
            
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
                    # 1. Extract Logo (if not found yet)
                    if not found_logo:
                        found_logo = extract_company_logo(site_resp.text, target_url)
                        if found_logo:
                             print(f"DEBUG: Found Logo: {found_logo}")

                    # 2. Extract Text
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
            "source_list": visited_sources_list,
            "logo": found_logo
        }}


    except Exception as e:
        print(f"CRITICAL AGENT 1 ERROR: {e}")
        yield {"type": "result", "payload": {"status": "error", "message": str(e)}}