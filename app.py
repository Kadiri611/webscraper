import xml.etree.ElementTree as ET
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import re
import tempfile
from flask import Flask, render_template, request, send_file

app = Flask(__name__)

def scrape_data(urls):
    # Set up the Selenium WebDriver (Chrome) with custom User-Agent
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run in headless mode (no UI)
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36")
    driver = webdriver.Chrome(options=options)

    root = ET.Element("Data")

    for url in urls:
        driver.get(url)

        # Wait for the modal gallery or any image elements to load (wait for specific class name)
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "_image__p95wJ"))
            )
        except:
            continue

        # Get the page source after rendering JavaScript
        page_source = driver.page_source

        # Use BeautifulSoup to parse the page
        soup = BeautifulSoup(page_source, 'html.parser')

        # Extract data from the page
        title = soup.find('h1').text if soup.find('h1') else "No title found"
        description = soup.find('p', class_='_content__om2Q_').text if soup.find('p', class_='_content__om2Q_') else "No description found"
        price = soup.find('h2', class_='_price__EH7rC').text if soup.find('h2', class_='_price__EH7rC') else "No price found"

        # Extract ad license number
        ad_license_element = soup.find('p', text="رخصة الإعلان")
        ad_license = ad_license_element.find_next('p', class_='_label___qjLO _brandText__qqCB1').text if ad_license_element else "No ad license found"

        # Extract all image URLs
        image_elements = soup.find_all('img', class_='_image__p95wJ')
        image_urls = [img['src'] for img in image_elements if 'src' in img.attrs]

        if not image_urls:
            all_images = soup.find_all('img')
            image_urls = [img['src'] for img in all_images if 'src' in img.attrs]

        # Filter image URLs using a regex pattern
        pattern = r'https://images\.aqar\.fm/webp/\d+x\d+/props/\d+_\d+\.jpg'
        filtered_image_urls = [img_url for img_url in image_urls if re.match(pattern, img_url)]

        # Create XML elements for the scraped data
        item = ET.SubElement(root, "Item")
        ET.SubElement(item, "Title").text = title
        ET.SubElement(item, "Description").text = description
        ET.SubElement(item, "Price").text = price
        ET.SubElement(item, "AdLicense").text = ad_license

        images_elem = ET.SubElement(item, "Images")
        for img_url in filtered_image_urls:
            ET.SubElement(images_elem, "ImageURL").text = img_url

    driver.quit()

    # Create a temporary file to save the XML output
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".xml")
    tree = ET.ElementTree(root)
    tree.write(temp_file.name)

    return temp_file.name

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/scrape', methods=['POST'])
def scrape():
    # Get the URLs entered by the user
    urls = request.form['urls'].splitlines()

    # Call the scrape_data function
    xml_file = scrape_data(urls)

    # Send the file to the user
    return send_file(xml_file, as_attachment=True, download_name="scraped_data.xml")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)

