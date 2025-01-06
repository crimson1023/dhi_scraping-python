import requests
import os
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

visited_urls = set()  # To track visited URLs

def url_join(current_url, relative_path):
    """
    Joins the current file's URL with a relative path to form a full URL.
    """
    return urljoin(current_url, relative_path)

def save_file(url):
    """
    Downloads the content of a URL and saves it locally, preserving the full path.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()

        # Parse the URL to construct the file path
        file_path = url2localpath(url)
        
        # Create directories if necessary
        dir_path = os.path.dirname(file_path)
        os.makedirs(dir_path, exist_ok=True)

        # Save the file
        with open(file_path, "wb") as file:
            file.write(response.content)
        
        print(f"File saved as: {file_path}")
        return response.text  # Return the response content for further scraping
    except requests.exceptions.RequestException as e:
        print(f"Failed to download {url}: {e}")
        return None

def get_all_links(content, current_url):
    """
    Extracts all href links from the content and converts them to absolute URLs.
    """
    soup = BeautifulSoup(content, "html.parser")
    
    # Find all anchor tags <a>
    anchor_tags = soup.find_all("a")
    hrefs = [url_join(current_url, tag.get("href")) for tag in anchor_tags if tag.get("href") and tag.get("href")[0] != "#"]
    
    # Find all CSS links <link rel="stylesheet">
    link_tags = soup.find_all("link", rel="stylesheet")
    css_hrefs = [url_join(current_url, tag.get("href")) for tag in link_tags if tag.get("href")]

    # Find all JavaScript links <script src="...">
    script_tags = soup.find_all("script", src=True)
    js_hrefs = [url_join(current_url, tag.get("src")) for tag in script_tags]

    # Find all image links <img src="...">
    img_tags = soup.find_all("img", src=True)
    img_hrefs = [url_join(current_url, tag.get("src")) for tag in img_tags]

    # Return combined hrefs for links, CSS, JS, and images
    return hrefs + css_hrefs + js_hrefs + img_hrefs

def url2localpath(url):
    parsed_url = urlparse(url)
    file_path = parsed_url.path.lstrip("/")

    return file_path

def scrape_url(current_url):
    """
    Scrapes the given URL, saving its content and recursively visiting all linked pages.
    """
    if current_url in visited_urls:
        return
    visited_urls.add(current_url)

    print(f"Scraping: {current_url}")
    response_text = save_file(current_url)
    if response_text is None:  # If the file couldn't be downloaded, skip further processing
        return

    # Extract and process all links
    hrefs = get_all_links(response_text, current_url)
    for href in hrefs:
        
        if href not in visited_urls and urlparse(href).netloc == urlparse(current_url).netloc and not os.path.exists(url2localpath(href)):
            scrape_url(href)

if __name__ == "__main__":
    start_url = "https://download.feflow.com/html/help100/feflow/02_News/news.html"
    scrape_url(start_url)
