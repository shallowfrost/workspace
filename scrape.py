import os
import time
import requests
import base64
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, WebDriverException

# ============================== CONFIGURATION ==============================

BASE_URL = 'https://allmanga.to/read/SFrub9DDGMrmdZWyh/solo-leveling/'
START_CHAPTER = 1
END_CHAPTER = 5
MAIN_FOLDER = "Chapters"

DSCROLL_SPEED = 0.007  # Time to wait between scrolls going down (seconds)
USCROLL_SPEED = 0.001  # Time to wait between scrolls going up (seconds)
SCROLL_STEP = 35    # Pixels to scroll each step
SCROLL_WAIT_TIME = 3  # Additional wait time after scrolling

IMAGE_DOWNLOAD_TIMEOUT = 5  # Timeout for downloading images (seconds)
MIN_IMAGE_SIZE = 100         # Minimum size (in bytes) for image downloads to be considered successful

ENABLE_HEADLESS = False
IGNORE_SSL_ERRORS = True
ALLOW_INSECURE_CONTENT = True

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
    'mgeko.cc': {
        'URL': 'https://www.mgeko.cc',
        'IMAGE_CSS_SELECTOR': '#chapter-reader img',
        'CHAPTER_URL_TEMPLATE': '{base_url}-chapter-{chapter}-eng-li/'
    }
}

# ============================== LOGGING SETUP ==============================

# Create a logs directory if it doesn't exist
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, 'manga_downloader.log')),
        logging.StreamHandler()
    ]
)

# ============================== FUNCTIONS ==============================

def get_domain(url):
    return url.split('/')[2]

def get_manga_settings(url):
    domain = get_domain(url)
    if domain in SITE_CONFIGURATIONS:
        return SITE_CONFIGURATIONS[domain]
    raise ValueError(f"No matching site settings found for domain: {domain}")

def validate_chapter_range(start, end):
    validated_start = max(start, 1)
    validated_end = max(end, validated_start)
    if end < start:
        logging.warning(f"End chapter ({end}) < start chapter ({start}). Setting end chapter to start.")
    return validated_start, validated_end

def setup_driver():
    options = webdriver.ChromeOptions()
    if IGNORE_SSL_ERRORS:
        options.add_argument('--ignore-certificate-errors')
    if ALLOW_INSECURE_CONTENT:
        options.add_argument('--allow-running-insecure-content')
    if ENABLE_HEADLESS:
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
    
    return webdriver.Chrome(options=options)

def generate_chapter_url(base_url, chapter, template):
    return template.format(base_url=base_url, chapter=chapter)

def scroll_page(driver):
    last_height = driver.execute_script("return document.body.scrollHeight")
    d_scroll_pause_time = DSCROLL_SPEED
    u_scroll_pause_time = USCROLL_SPEED
    scroll_increment = SCROLL_STEP

    # Scroll down in increments
    while True:
        driver.execute_script(f"window.scrollBy(0, {scroll_increment});")
        time.sleep(d_scroll_pause_time)

        new_height = driver.execute_script("return document.body.scrollHeight")

        if new_height > last_height:
            last_height = new_height
        else:
            # Check if near the bottom
            viewport_height = driver.execute_script("return window.innerHeight")
            scroll_position = driver.execute_script("return window.scrollY + window.innerHeight")
            if scroll_position >= last_height - 10:
                break

    # Wait for any remaining content to load
    time.sleep(SCROLL_WAIT_TIME)

    # Scroll back to the top smoothly
    current_position = driver.execute_script("return window.scrollY")
    while current_position > 0:
        decrement = scroll_increment if current_position >= scroll_increment else current_position
        driver.execute_script(f"window.scrollBy(0, {-decrement});")
        time.sleep(u_scroll_pause_time)
        current_position -= decrement

    # Ensure the page is at the top
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(u_scroll_pause_time)

def download_image(image_url, path, chapter_num, image_num):
    try:
        if image_url.startswith('data:'):
            # Handle base64 encoded images
            data = image_url.split(',')[1]
            decoded_data = base64.b64decode(data)
            with open(path, 'wb') as file:
                file.write(decoded_data)
            image_size = len(decoded_data)
            if image_size < MIN_IMAGE_SIZE:
                logging.warning(f"Failed to download image (size below minimum): {os.path.basename(path)} | Size: {image_size} bytes")
                return 0
            else:
                logging.info(f"Downloaded base64 image: {os.path.basename(path)} | Size: {image_size} bytes")
                return image_size
        else:
            # Handle regular image URLs
            response = requests.get(image_url, timeout=IMAGE_DOWNLOAD_TIMEOUT)
            response.raise_for_status()
            image_size = len(response.content)
            if image_size < MIN_IMAGE_SIZE:
                logging.warning(f"Failed to download image (size below minimum): {image_url}")
                return 0
            else:
                with open(path, 'wb') as file:
                    file.write(response.content)
                logging.info(f"Downloaded image: {os.path.basename(path)} | Size: {image_size} bytes")
                return image_size
    except Exception as e:
        logging.error(f"Failed to download image: {image_url} | Error: {e}")
        return 0

def download_chapter(driver, url, chapter_num, folder, selector):
    try:
        driver.get(url)
        time.sleep(5)  # Allow the page to load
        scroll_page(driver)
        images = driver.find_elements(By.CSS_SELECTOR, selector)
        image_urls = [img.get_attribute('src') for img in images]

        chapter_folder = os.path.join(folder, f"Chapter_{chapter_num}")
        os.makedirs(chapter_folder, exist_ok=True)

        chapter_size = 0
        downloaded = 0
        failed = 0

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(
                    download_image,
                    image_url=image_url,
                    path=os.path.join(chapter_folder, f"{chapter_num:03d}_{i:03d}.png"),
                    chapter_num=chapter_num,
                    image_num=i
                ): i for i, image_url in enumerate(image_urls, 1)
            }
            for future in as_completed(futures):
                size = future.result()
                if size:
                    chapter_size += size
                    downloaded += 1
                else:
                    failed += 1

        logging.info(f"Chapter {chapter_num} complete: {downloaded} downloaded | {failed} failed | Total size: {chapter_size / 1024:.2f} KB")
        return chapter_size, downloaded, failed

    except (TimeoutException, WebDriverException) as e:
        logging.error(f"Error loading chapter {chapter_num} page: {e}")
        return 0, 0, 1

def download_all_chapters(driver, start, end, base_url, template, selector):
    os.makedirs(MAIN_FOLDER, exist_ok=True)
    total_size = 0
    total_downloaded = 0
    total_failed = 0

    for chapter in range(start, end + 1):
        chapter_url = generate_chapter_url(base_url, chapter, template)
        logging.info(f"Starting download for Chapter {chapter}")
        size, downloaded, failed = download_chapter(driver, chapter_url, chapter, MAIN_FOLDER, selector)
        total_size += size
        total_downloaded += downloaded
        total_failed += failed

    logging.info(f"Download Summary: {total_downloaded} images downloaded | {total_failed} failed | Total size: {total_size / 1024:.2f} KB")

# ============================== MAIN EXECUTION ==============================

if __name__ == '__main__':
    try:
        settings = get_manga_settings(BASE_URL)
        start_chap, end_chap = validate_chapter_range(START_CHAPTER, END_CHAPTER)

        logging.info(f"Starting manga downloader: Chapters {start_chap} to {end_chap}, {(end_chap - start_chap + 1)} total")
        with setup_driver() as driver:
            download_all_chapters(
                driver,
                start=start_chap,
                end=end_chap,
                base_url=BASE_URL,
                template=settings['CHAPTER_URL_TEMPLATE'],
                selector=settings['IMAGE_CSS_SELECTOR']
            )
        logging.info("Manga download process completed successfully.")
    except Exception as e:
        logging.critical(f"An unexpected error occurred: {e}")
