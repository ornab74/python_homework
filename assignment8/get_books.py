from pathlib import Path
import json
import time

import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


# Task 3: URL for the Durham County Library search
SEARCH_URL = (
    "https://durhamcounty.bibliocommons.com/v2/search"
    "?query=learning%20spanish&searchType=smart"
)

BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "get_books.csv"
JSON_PATH = BASE_DIR / "get_books.json"


def create_driver():
    # Task 3: Create Selenium driver
    options = webdriver.ChromeOptions()

    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(
        service=ChromeService(ChromeDriverManager().install()),
        options=options,
    )

    return driver


def main():
    driver = create_driver()

    try:
        # Task 3: Load the search page
        driver.get(SEARCH_URL)

        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "li.cp-search-result-item")
            )
        )

        time.sleep(2)

        # Task 3: Find all search result li elements
        search_results = driver.find_elements(
            By.CSS_SELECTOR,
            "li.cp-search-result-item",
        )

        print(f"Found {len(search_results)} search results")

        # Task 3: Required empty results list
        results = []

        # Task 3: Extract each book
        for item in search_results:

            # Find title
            title_element = item.find_element(
                By.CSS_SELECTOR,
                "a.cp-title-link",
            )

            title = title_element.text.strip()

            # Find all authors
            author_elements = item.find_elements(
                By.CSS_SELECTOR,
                "a.author-link",
            )

            authors = []

            for author_element in author_elements:
                author = author_element.text.strip()

                if author:
                    authors.append(author)

            # Join multiple authors with semicolon
            author_text = "; ".join(authors)

            # Find format and publication year
            format_element = item.find_element(
                By.CSS_SELECTOR,
                "span.display-info-primary",
            )

            format_year = format_element.text.strip()

            # Task 3: Create the required dictionary directly
            book = {
                "Title": title,
                "Author": author_text,
                "Format-Year": format_year,
            }

            # Add dictionary to results
            results.append(book)

        # Task 3: Create and print DataFrame
        df = pd.DataFrame(results)

        print(df)

        # Task 4: Write CSV
        df.to_csv(
            CSV_PATH,
            index=False,
        )

        # Task 4: Write JSON
        with open(
            JSON_PATH,
            "w",
            encoding="utf-8",
        ) as json_file:
            json.dump(
                results,
                json_file,
                indent=2,
            )

        print(f"Wrote {CSV_PATH}")
        print(f"Wrote {JSON_PATH}")

    finally:
        driver.quit()


if __name__ == "__main__":
    main()
