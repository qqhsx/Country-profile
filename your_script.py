import requests
from bs4 import BeautifulSoup
import json
import re
import os
from googletrans import Translator

def sanitize_filename(title):
    return re.sub(r'[<>:"/\\|?*]', '_', title)

def fetch_html(url):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return BeautifulSoup(response.text, 'html.parser')
    else:
        print(f"Error fetching {url}: Status code {response.status_code}")
        return None

def scrape_links_from_search(base_url, num_pages=1):
    all_results = []
    for page in range(1, num_pages + 1):
        soup = fetch_html(f"{base_url}{page}")
        if soup:
            results_container = soup.find('div', class_='ssrcss-1v7bxtk-StyledContainer enjd40x0')
            if results_container:
                results = results_container.find_all('a', class_='ssrcss-its5xf-PromoLink exn3ah91')
                for result in results:
                    title = result.get_text(strip=True)
                    link = result['href']
                    if not link.startswith('http'):
                        link = 'https://www.bbc.co.uk' + link
                    all_results.append((title, link))
                    print(f"Found title: {title}, Link: {link}")
            else:
                print("No search results container found.")
    return all_results

def scrape_article_content(link, title, output_directory):
    translator = Translator()
    soup = fetch_html(link)
    if not soup:
        return

    # Fetching and translating the title
    page_title = soup.find('h1').text if soup.find('h1') else "No Title"
    
    try:
        translated_title = translator.translate(page_title, dest='zh-cn').text
    except Exception as e:
        print(f"Translation error for title '{page_title}': {e}")
        translated_title = "翻译失败"

    print(f'Processing page title: {page_title} (Translated: {translated_title})')

    main_content = soup.find('div', class_='ssrcss-1ki8hfp-StyledZone e1mcntqj3')
    content_data = {'title': translated_title, 'link': link, 'content': []}

    if main_content:
        for element in main_content.find_all(['p', 'img']):
            if element.name == 'p':
                full_paragraph = element.get_text(strip=True)

                # Translate the paragraph to Chinese with error handling
                try:
                    if full_paragraph:  # Check if the paragraph is not empty
                        translated_paragraph = translator.translate(full_paragraph, dest='zh-cn').text
                        content_data['content'].append({"type": "paragraph", "content": translated_paragraph})
                    else:
                        print("Empty paragraph, skipping.")
                except Exception as e:
                    print(f"Translation error for paragraph: {e}. Skipping this paragraph.")
            elif element.name == 'img':
                img_url = element['src']
                content_data['content'].append({"type": "image", "content": img_url})
    else:
        print("Main content section not found.")

    # Ensure output directory exists
    os.makedirs(output_directory, exist_ok=True)
    filename = os.path.join(output_directory, f"{sanitize_filename(translated_title)}.json")
    with open(filename, 'w', encoding='utf-8') as json_file:
        json.dump(content_data, json_file, ensure_ascii=False, indent=4)
    print(f"Content saved to {filename}")

# Base URL for search with page parameter
base_url = "https://www.bbc.co.uk/search?q=profile+-+Timeline&d=NEWS_GNL&page="
num_pages = 22  # Adjust the number of pages as needed
output_directory = 'output'  # Specify the output directory

# Step 1: Fetch all article links
all_results = scrape_links_from_search(base_url, num_pages)

# Step 2: Fetch content for each article link
for title, link in all_results:
    scrape_article_content(link, title, output_directory)
