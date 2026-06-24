import sys
import os
from bs4 import BeautifulSoup
import requests

from config import Config
import monitor

def test_live_movie(url):
    print("==================================================")
    print(f"LIVE TEST RUN FOR URL:")
    print(f"Target: {url}")
    print("==================================================")
    
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
    }
    
    try:
        print("Fetching page...")
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        html = response.text
        print(f"Successfully fetched page. HTML Size: {len(html)} characters.")
    except Exception as e:
        print(f"ERROR: Failed to fetch the page: {e}")
        return False
        
    print("\nParsing HTML structure...")
    soup = BeautifulSoup(html, "html.parser")
    
    # 1. Print title
    title = soup.title.text.strip() if soup.title else "No Title Found"
    print(f"Page Title: {title}")
    
    # 2. Check for target tickets button
    print("\nSearching for ticket booking button (<a> tag with class='cgv-btn' and text containing 'Hemen Bilet Al')...")
    anchors = soup.find_all("a", class_="cgv-btn")
    
    found_tickets = False
    for a in anchors:
        href = a.get("href", "")
        text = a.get_text().strip()
        print(f" -> Found cgv-btn anchor: href='{href}', text='{text}'")
        if "/biletleme/" in href.lower() and "hemen bilet al" in text.lower():
            found_tickets = True
            print("    [!] MATCH: This is a valid ticket button!")
            
    # 3. Check other elements with similar text/links just for diagnostic information
    print("\nDiagnostics:")
    hemen_bilet_al_occurrences = html.lower().count("hemen bilet al")
    biletleme_occurrences = html.lower().count("/biletleme/")
    cgv_btn_occurrences = html.lower().count("cgv-btn")
    print(f" - Raw 'hemen bilet al' text occurrences: {hemen_bilet_al_occurrences}")
    print(f" - Raw '/biletleme/' URL occurrences: {biletleme_occurrences}")
    print(f" - Raw 'cgv-btn' CSS class occurrences: {cgv_btn_occurrences}")
    
    print("\n==================================================")
    if found_tickets:
        print("RESULT: TICKETS ARE ON SALE!")
    else:
        print("RESULT: TICKETS ARE NOT ON SALE YET.")
    print("==================================================")
    return True

if __name__ == "__main__":
    target_url = "https://www.paribucineverse.com/fantastik-filmleri/supergirl-filmi-izle"
    if len(sys.argv) > 1:
        target_url = sys.argv[1]
        
    test_live_movie(target_url)
