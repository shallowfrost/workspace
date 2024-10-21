import os
import time
import requests
import base64
import logging
from concurrent.futures import ThreadPoolExecutor
from selenium import webdriver
from selenium.webdriver.common.by import By

# ============================== MANUAL CONFIGURATION ==============================

# Initial URL setup and chapter range
BASE_URL = 'https://nitroscans.net/series/super-god-system'
START_CHAPTER = 1
END_CHAPTER = 5

# Save folder
MAIN_FOLDER = "Chapters"

# Web scraping settings
SCROLL_SPEED = 0.1
SCROLL_STEP = 1000
SCROLL_WAIT_TIME = 3  # Time to wait between each scroll
IMAGE_DOWNLOAD_TIMEOUT = 10  # Timeout for downloading images (seconds)
MIN_IMAGE_SIZE = 100  # Minimum size (in bytes) for images to be considered valid

# WebDriver options
ENABLE_HEADLESS = False
IGNORE_SSL_ERRORS = True
ALLOW_INSECURE_CONTENT = True

# Dictionary to hold configurations for each site
SITE_CONFIGURATIONS = {
    'allmanga.to': {
        'URL': 'https://allmanga.to/manga?cty=ALL',
        'IMAGE_CSS_SELECTOR': '#pictureViewer img.img.noselect',
        'CHAPTER_URL_TEMPLATE': '{base_url}/chapter-{chapter}-sub'
    },
    'mangaread.org': {
        'URL': 'https://www.mangaread.org',
        'IMAGE_CSS_SELECTOR': 'img.wp-manga-chapter-img',
        'CHAPTER_URL_TEMPLATE': '{base_url}/chapter-{chapter}/'
    },
    'nitroscans.net': {
        'URL': 'https://nitroscans.net',
        'IMAGE_CSS_SELECTOR': 'img.wp-manga-chapter-img',
        'CHAPTER_URL_TEMPLATE': '{base_url}/chapter-{chapter}/'
    },
    'mgeko.cc': {
        'URL': 'https://www.mgeko.cc',
        'IMAGE_CSS_SELECTOR': '#chapter-reader img',
        'CHAPTER_URL_TEMPLATE': '{base_url}-chapter-{chapter}-eng-li/'
    }
}

# ============================== END OF MANUAL CONFIGURATION ==============================

# Set up logging for better error tracking
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Function to determine settings based on the URL's domain
def get_manga_settings(url):
    domain = url.split('/')[2]
    if domain in SITE_CONFIGURATIONS:
        return SITE_CONFIGURATIONS[domain]
    raise ValueError("No matching site settings found.")

# Function to validate chapter range
def validate_chapter_range(start, end):
    if start < 1:
        raise ValueError("Start chapter must be at least 1.")
    if end < start:
        logging.warning("End chapter is less than start chapter. Setting end chapter to start.")
        return start
    return end

# Function to set up the Selenium WebDriver
def driver_setup():
    options = webdriver.ChromeOptions()
    if IGNORE_SSL_ERRORS:
        options.add_argument('--ignore-certificate-errors')
    if ALLOW_INSECURE_CONTENT:
        options.add_argument('--allow-running-insecure-content')
    if ENABLE_HEADLESS:
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
    return webdriver.Chrome(options=options)

# Function to generate the chapter URL
def generate_chapter_url(base_url, chapter, url_template):
    return url_template.format(base_url=base_url, chapter=chapter)

# Function to download all chapters
def download_all_chapters(driver, start_chapter, end_chapter, base_url, chapter_url_template, image_css_selector, max_retries=3):
    overall_start_time = time.time()
    total_images_downloaded = 0
    total_size_downloaded = 0
    total_errors = 0

    for chapter in range(start_chapter, end_chapter + 1):
        chapter_size = 0
        downloaded_images = 0
        errors = 0
        attempts = 0

        # Retry loop for downloading the chapter if errors occur
        while attempts < max_retries:
            chapter_url = generate_chapter_url(base_url, chapter, chapter_url_template)
            chapter_size, downloaded_images, errors = download_chapter(
                driver, chapter_url, chapter, MAIN_FOLDER, image_css_selector
            )

            if errors == 0:
                # If no errors, break out of the retry loop
                break
            else:
                # Log the retry attempt and increment the counter
                attempts += 1
                logging.warning(f"Errors occurred during Chapter {chapter} download. Attempt {attempts}/{max_retries}. Retrying...")

        if errors > 0:
            logging.error(f"Failed to download Chapter {chapter} after {max_retries} attempts. Skipping chapter.")

        total_images_downloaded += downloaded_images
        total_size_downloaded += chapter_size
        total_errors += errors

    overall_elapsed_time = time.time() - overall_start_time
    logging.info(f"Overall download complete.")
    logging.info(f"Chapters: {start_chapter}-{end_chapter}")
    logging.info(f"Total images: {total_images_downloaded}")
    logging.info(f"Total size: {total_size_downloaded / 1024:.2f} KB")
    logging.info(f"Total time: {overall_elapsed_time:.2f} seconds")
    logging.info(f"Errors: {total_errors}.")

# Function to handle page scrolling
def scroll_page(driver, wait_time, scroll_speed=0.1, scroll_step=100):

    last_height = driver.execute_script("return document.body.scrollHeight")
    
    while True:
        # Scroll down by the specified step size
        driver.execute_script(f"window.scrollBy(0, {scroll_step});")
        time.sleep(scroll_speed)

        # Calculate new scroll height after each scroll
        new_height = driver.execute_script("return document.body.scrollHeight")

        # If the height doesn't change, we've reached the bottom
        if new_height == last_height:
            break
        last_height = new_height

    # Wait for images to load if needed
    time.sleep(wait_time)

    # Scroll back to the top
    driver.execute_script("window.scrollTo(0, 0);")

# Function to download images for a single chapter
def download_chapter(driver, chapter_url, chapter_number, main_folder, image_css_selector):
    logging.info(f"Downloading images for Chapter {chapter_number}")
    chapter_start_time = time.time()
    driver.get(chapter_url)
    time.sleep(5)
    scroll_page(driver, SCROLL_WAIT_TIME, SCROLL_SPEED, SCROLL_STEP)

    image_elements = driver.find_elements(By.CSS_SELECTOR, image_css_selector)
    image_urls = [image.get_attribute('src') for image in image_elements]

    chapter_folder = os.path.join(main_folder, f"Chapter_{chapter_number}")
    os.makedirs(chapter_folder, exist_ok=True)

    chapter_size = 0
    downloaded_images = 0
    errors = 0

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [
            executor.submit(
                download_image, image_url, chapter_folder, chapter_number, image_number
            )
            for image_number, image_url in enumerate(image_urls, 1)
        ]
        for future in futures:
            try:
                image_size = future.result()
                if image_size:
                    chapter_size += image_size
                    downloaded_images += 1
                else:
                    errors += 1
            except Exception as e:
                logging.error(f"Error downloading image: {e}")
                errors += 1

    chapter_time_elapsed = time.time() - chapter_start_time
    logging.info(f"Chapter {chapter_number} download complete. {downloaded_images} images downloaded, total size: {chapter_size / 1024:.2f} KB, time elapsed: {chapter_time_elapsed:.2f} seconds, errors: {errors}.")
    return chapter_size, downloaded_images, errors

# Function to download a single image
def download_image(image_url, chapter_folder, chapter_number, image_number):
    try:
        file_name = f"{chapter_number:03d}_{image_number:03d}.png"
        file_path = os.path.join(chapter_folder, file_name)

        if image_url.startswith('data:'):
            data = image_url.split(',')[1]
            decoded_data = base64.b64decode(data)
            with open(file_path, 'wb') as file:
                file.write(decoded_data)
            image_size = len(decoded_data)
            logging.info(f"Downloaded base64 image {file_name} of size {image_size} bytes.")
            return image_size
        else:
            response = requests.get(image_url, timeout=IMAGE_DOWNLOAD_TIMEOUT)
            response.raise_for_status()
            image_size = len(response.content)
            if image_size > MIN_IMAGE_SIZE:
                with open(file_path, 'wb') as file:
                    file.write(response.content)
                logging.info(f"Downloaded image {file_name} of size {image_size} bytes.")
                return image_size
    except (requests.exceptions.RequestException, requests.exceptions.HTTPError) as e:
        logging.error(f"Error downloading image {image_url}: {e}")
        return None

# Main script execution
if __name__ == '__main__':
    settings = get_manga_settings(BASE_URL)
    IMAGE_CSS_SELECTOR = settings['IMAGE_CSS_SELECTOR']
    CHAPTER_URL_TEMPLATE = settings['CHAPTER_URL_TEMPLATE']

    # Validate chapter range
    END_CHAPTER = validate_chapter_range(START_CHAPTER, END_CHAPTER)
    os.makedirs(MAIN_FOLDER, exist_ok=True)

    # Start the WebDriver and download chapters
    with driver_setup() as driver:
        download_all_chapters(driver, START_CHAPTER, END_CHAPTER, BASE_URL, CHAPTER_URL_TEMPLATE, IMAGE_CSS_SELECTOR)
