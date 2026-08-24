from pathlib import Path
import json
import re
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

# Task 2 / Task 3: selectors taken from the inspected search-result DOM.
# Every title, author, and format/year lookup is scoped to one result <li>.
RESULT_SELECTOR = "li.row.cp-search-result-item"
TITLE_SELECTOR = "h3.cp-title span.title-content"
AUTHOR_LINK_SELECTOR = "span.cp-author-link a.author-link"
AUTHOR_LINK_FALLBACK_SELECTOR = "a.author-link"
AUTHOR_CONTAINER_SELECTOR = "span.cp-author-link"
FORMAT_YEAR_CONTAINER_SELECTOR = "div.cp-format-info"
FORMAT_YEAR_SELECTOR = "span.display-info-primary"


def create_driver():
    # Task 3: Create Selenium driver
    options = webdriver.ChromeOptions()

    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")

    return webdriver.Chrome(
        service=ChromeService(ChromeDriverManager().install()),
        options=options,
    )


def normalize_text(value):
    """Collapse whitespace from text read by Selenium."""
    return " ".join((value or "").split())


def first_text(parent, selectors):
    """Return the first non-empty text found by the supplied selectors."""
    for selector in selectors:
        for element in parent.find_elements(By.CSS_SELECTOR, selector):
            text = normalize_text(element.text)
            if text:
                return text

    return ""


def extract_authors(item):
    """Extract and de-duplicate all authors within one result element."""
    # The inspected structure is span.cp-author-link > a.author-link.
    # The broader fallbacks handle a moved link or an author rendered as text.
    author_elements = item.find_elements(
        By.CSS_SELECTOR,
        AUTHOR_LINK_SELECTOR,
    )

    if not author_elements:
        author_elements = item.find_elements(
            By.CSS_SELECTOR,
            AUTHOR_LINK_FALLBACK_SELECTOR,
        )

    raw_authors = [element.text for element in author_elements]

    if not any(normalize_text(author) for author in raw_authors):
        author_containers = item.find_elements(
            By.CSS_SELECTOR,
            AUTHOR_CONTAINER_SELECTOR,
        )
        raw_authors = [element.text for element in author_containers]

    authors = []
    seen = set()

    for raw_author in raw_authors:
        author = normalize_text(raw_author)
        author = re.sub(r"^by\s+", "", author, flags=re.IGNORECASE)
        author = author.strip(" ;\u2022")

        key = author.casefold()
        if author and key not in seen:
            authors.append(author)
            seen.add(key)

    # Missing author markup produces an empty value instead of an exception.
    return "; ".join(authors)


def extract_book(item):
    """Extract one book dictionary from one search-result <li>."""
    title = first_text(
        item,
        [
            TITLE_SELECTOR,
            "h3.cp-title a",
            "h3.cp-title",
        ],
    )

    author_text = extract_authors(item)

    # Task 3 specifically asks for the span inside the format/year div.
    format_year = ""
    format_containers = item.find_elements(
        By.CSS_SELECTOR,
        FORMAT_YEAR_CONTAINER_SELECTOR,
    )

    if format_containers:
        format_year = first_text(
            format_containers[0],
            [FORMAT_YEAR_SELECTOR, "span.display-info"],
        )

    return {
        "Title": title,
        "Author": author_text,
        "Format-Year": format_year,
    }


def main():
    driver = create_driver()

    try:
        # Task 3: Load the search page
        driver.get(SEARCH_URL)

        WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, RESULT_SELECTOR)
            )
        )

        time.sleep(2)

        # Task 3: Find the result li elements by tag and inspected classes.
        search_results = driver.find_elements(
            By.CSS_SELECTOR,
            RESULT_SELECTOR,
        )

        print(f"Found {len(search_results)} search results")

        # Task 3: Required empty list, then append one dict per result li.
        results = []

        for item in search_results:
            book = extract_book(item)
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
                ensure_ascii=False,
            )

        print(f"Wrote {CSV_PATH}")
        print(f"Wrote {JSON_PATH}")

    finally:
        driver.quit()


if __name__ == "__main__":
    main()
