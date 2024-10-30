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

    main_content = soup.find('div', class_='ssrcss-1ki8hfp-StyledZone')
    content_data = {'title': translated_title, 'link': link, 'content': []}

    if main_content:
        # Process p, img, and h2 elements
        for element in main_content.find_all(['p', 'img', 'h2']):
            if element.name == 'p':
                full_paragraph = element.get_text(strip=True)
                try:
                    if full_paragraph:
                        translated_paragraph = translator.translate(full_paragraph, dest='zh-cn').text
                        content_data['content'].append({"type": "paragraph", "content": translated_paragraph})
                except Exception as e:
                    print(f"Translation error for paragraph: {e}. Skipping this paragraph.")
            elif element.name == 'img':
                img_url = element['src']
                content_data['content'].append({"type": "image", "content": img_url})
            elif element.name == 'h2':  # Process h2 tags
                heading_text = element.get_text(strip=True)
                try:
                    translated_heading = translator.translate(heading_text, dest='zh-cn').text
                    content_data['content'].append({"type": "heading", "content": translated_heading})
                except Exception as e:
                    print(f"Translation error for heading '{heading_text}': {e}")
                    
    else:
        print("Main content section not found.")

    # Ensure output directory exists
    os.makedirs(output_directory, exist_ok=True)
    filename = os.path.join(output_directory, f"{sanitize_filename(translated_title)}.json")
    with open(filename, 'w', encoding='utf-8') as json_file:
        json.dump(content_data, json_file, ensure_ascii=False, indent=4)
    print(f"Content saved to {filename}")
