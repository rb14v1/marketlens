import requests
from urllib.parse import urlparse

def get_company_logo(company_name, homepage_url):
    """
    Fetches the company logo using Clearbit API first, then falls back to Google Favicons.
    Prioritizes the official homepage found during scraping.
    """
    domain = ""
    
    # 1. Try to extract domain from the URL found by the search agent
    if homepage_url:
        try:
            parsed = urlparse(homepage_url)
            domain = parsed.netloc.replace("www.", "")
        except:
            pass
    
    # 2. If no URL provided, try to guess domain from company name (clean spaces)
    if not domain and company_name:
        domain = f"{company_name.replace(' ', '').lower()}.com"

    if not domain:
        return None

    # 3. Try Clearbit API (High Quality)
    # We use a fast timeout to check if the image exists without downloading the whole thing yet
    clearbit_url = f"https://logo.clearbit.com/{domain}"
    try:
        if requests.head(clearbit_url, timeout=1.5).status_code == 200:
            return clearbit_url
    except:
        pass

    # 4. Fallback to Google Favicon (Reliable)
    return f"https://www.google.com/s2/favicons?domain={domain}&sz=128"