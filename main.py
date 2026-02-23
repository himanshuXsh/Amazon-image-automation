# main.py

import os
import re
import time
import requests
import pandas as pd

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

from webdriver_manager.chrome import ChromeDriverManager

# ================== CONFIG ==================

EXCEL_FILE = "PRODUCT_LIST.xlsx"   # Columns: PRODUCT_NAME, PRODUCT_URL
SHEET_NAME = "Sheet1"
WAIT_TIME = 20                     # Selenium wait (sec)
HOVER_DELAY = 0.7                  # Delay between thumb hovers
DOWNLOAD_DELAY = 0.4               # Delay between downloads

MAX_IMAGES_PER_PRODUCT = 5         # <-- tumhari requirement

# ============================================


def clean_name(name: str) -> str:
    """Safe string for folder/filename."""
    name = str(name).strip()
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    name = re.sub(r'\s+', '_', name)
    return name[:80]


def get_hi_res_image(url: str) -> str | None:
    """
    Amazon image URL ko clean karo lekin SL/UL size ko respect karo.
    Example:
      .../I/abcd._SX450_.jpg   -> .../I/abcd.jpg
      .../I/abcd._SL1500_.jpg  -> as is (1500px main image)
    """
    if not url or "media-amazon.com" not in url:
        return None

    # Already hi-res SL/UL ho to untouched
    if "._SL" in url or "._UL" in url:
        return url

    # Generic modifiers (SX, SY, SS, AC, etc.) hatao
    return re.sub(r'\._[A-Z]{2,}[0-9,]*_\.', '.', url)


def setup_driver() -> webdriver.Chrome:
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.maximize_window()
    return driver


def interact_with_gallery(driver: webdriver.Chrome) -> list:
    """
    Sirf top N (MAX_IMAGES_PER_PRODUCT) thumbnails ko hover + click karo,
    taaki unke hi-res URLs load ho jaayen. Unhi thumbs ki ordered list
    return karega.
    """
    driver.execute_script("window.scrollTo(0, 800);")
    time.sleep(2)

    # Visible thumbs
    thumbs = driver.find_elements(
        By.CSS_SELECTOR,
        "#altImages li:not(.aok-hidden) img"
    )
    thumbs = thumbs[:MAX_IMAGES_PER_PRODUCT]  # max N
    actions = ActionChains(driver)

    ordered_thumbs = []
    for thumb in thumbs:
        try:
            actions.move_to_element(thumb).perform()
            time.sleep(HOVER_DELAY)
            driver.execute_script("arguments[0].click();", thumb)
            time.sleep(0.8)
            ordered_thumbs.append(thumb)
        except Exception:
            continue

    # Light scroll (lazy-load safety)
    for _ in range(2):
        driver.execute_script("window.scrollBy(0, 300);")
        time.sleep(0.8)
        driver.execute_script("window.scrollBy(0, -200);")
        time.sleep(0.8)

    return ordered_thumbs


def extract_image_urls(driver: webdriver.Chrome, ordered_thumbs: list) -> list[str]:
    """
    Har thumbnail ke liye exactly ek hi-res URL nikaalo, gallery order maintain karo.
    Max: MAX_IMAGES_PER_PRODUCT.
    """
    urls: list[str] = []

    # Single-image listing (no thumbs)
    if not ordered_thumbs:
        try:
            main_img = driver.find_element(
                By.CSS_SELECTOR, "#landingImage, #main-image-container img"
            )
            src = main_img.get_attribute("data-old-hires") or main_img.get_attribute("src")
            hi = get_hi_res_image(src)
            if hi:
                urls.append(hi)
        except Exception:
            pass
        return urls

    for thumb in ordered_thumbs:
        hi_url = None

        # 1) data-a-dynamic-image (JSON-like string)
        data_dyn = thumb.get_attribute("data-a-dynamic-image")
        if data_dyn:
            m = re.search(r'https?://[^"\s}]+', data_dyn)
            if m:
                hi_url = m.group()

        # 2) Fallback: data-old-hires / src
        if not hi_url:
            src = (
                thumb.get_attribute("data-old-hires")
                or thumb.get_attribute("src")
                or ""
            )
            if src:
                hi_url = src

        if hi_url:
            hi = get_hi_res_image(hi_url)
            if hi and hi not in urls:   # order + no dup
                urls.append(hi)

        if len(urls) >= MAX_IMAGES_PER_PRODUCT:
            break

    return urls


def download_images(urls: list[str], folder: str, base_name: str) -> None:
    """Download URLs as BASE_1.jpg, BASE_2.jpg ... into folder."""
    os.makedirs(folder, exist_ok=True)

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        ),
        "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
        "Referer": "https://www.amazon.in/",
    }

    session = requests.Session()
    session.headers.update(headers)

    print(f"  → downloading {len(urls)} images")

    for idx, url in enumerate(urls, start=1):
        filename = f"{base_name}_{idx}.jpg"
        path = os.path.join(folder, filename)

        try:
            resp = session.get(url, stream=True, timeout=30)
            resp.raise_for_status()
            with open(path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            print(f"    [OK] {filename}")
        except Exception as e:
            print(f"    [ERR] {filename} -> {e}")

        time.sleep(DOWNLOAD_DELAY)


def main() -> None:
    # Excel: PRODUCT_NAME, PRODUCT_URL
    df = pd.read_excel(EXCEL_FILE, sheet_name=SHEET_NAME)

    driver = setup_driver()
    wait = WebDriverWait(driver, WAIT_TIME)

    for _, row in df.iterrows():
        product_name = row["PRODUCT_NAME"]
        product_url = row["PRODUCT_URL"]

        base_name = clean_name(product_name)           # folder & filename base
        out_folder = os.path.join(os.getcwd(), base_name)

        print("\n====================================================")
        print(f"PRODUCT_NAME : {product_name}")
        print(f"URL          : {product_url}")
        print(f"FOLDER       : {out_folder}")
        print("====================================================")

        try:
            driver.get(product_url)
        except Exception as e:
            print(f"[SKIP] cannot open URL: {e}")
            continue

        try:
            wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "#landingImage, #main-image-container img")
                )
            )
        except Exception:
            print("  ! main image not found, skipping")
            continue

        time.sleep(2)

        # Load top N gallery images
        ordered_thumbs = interact_with_gallery(driver)
        time.sleep(2)

        # Extract hi-res URLs in order
        urls = extract_image_urls(driver, ordered_thumbs)
        print(f"  final images (max {MAX_IMAGES_PER_PRODUCT}): {len(urls)}")

        if not urls:
            print("  ! no images extracted")
            continue

        # Download as PRODUCT_NAME_1.jpg, PRODUCT_NAME_2.jpg, ...
        download_images(urls, out_folder, base_name)

        time.sleep(3)   # polite delay between products

    driver.quit()
    print("\nDONE ✅")


if __name__ == "__main__":
    main()
