from __future__ import annotations
from dataclasses import asdict, dataclass
from pathlib import Path
import json
import time
import pandas as pd
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


SEARCH_URL = "https://durhamcounty.bibliocommons.com/v2/search?query=learning%20spanish&searchType=smart"
BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "get_books.csv"
JSON_PATH = BASE_DIR / "get_books.json"

@dataclass(slots=True)

class BookResult:
    Title: str
    Author: str
    Format_Year: str



def create_driver(headless: bool = True) -> webdriver.Chrome:
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--user-agent=CTD-assignment8-student-browser/1.0")

    return webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)

def first_text(element, selectors: list[str]) -> str:
    for selector in selectors:
        try:
            found = element.find_element(By.CSS_SELECTOR, selector)
            text = found.text.strip()
            if text:
                return text
        except NoSuchElementException:
            pass
    return ""

def many_texts(element, selectors: list[str]) -> list[str]:
    values: list[str] = []
    for selector in selectors:
        for found in element.find_elements(By.CSS_SELECTOR, selector):
            text = found.text.strip()
            if text and text not in values:
                values.append(text)
        if values:
            break
    return values

def extract_books(driver: webdriver.Chrome) -> list[BookResult]:

    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, "body")))
    time.sleep(2)
    result_selectors = [

        "li.cp-search-result-item",
        "li[class*='cp-search-result']",
        "li[data-test-id*='searchResult']",
        "li:has(a[href*='/v2/record/'])",
    ]

    items = []

    for selector in result_selectors:
        try:
            items = driver.find_elements(By.CSS_SELECTOR, selector)
            if items:
                break
        except WebDriverException:
            continue

    books: list[BookResult] = []
    for item in items:
        title = first_text(item, [
            "a[data-test-id*='title']",
            "a.title-content-title",
            "a.cp-title-link",
            "a[href*='/v2/record/']",
            "h2 a",
            "h3 a",
        ])

        authors = many_texts(item, [
            "a[href*='author']",
            "a.author-link",
            "span.cp-author-link a",
            "div[class*='author'] a",
        ])

        format_year = first_text(item, [
            "span.display-info-primary",
            "div[class*='format'] span",
            "span[class*='display-info']",
            "div[class*='bib-format']",
        ])

        if title:

            books.append(BookResult(
                Title=title,
                Author="; ".join(authors) if authors else "Unknown",
                Format_Year=format_year or "Unknown",
            ))


    return books

def main() -> None:
    driver = create_driver(headless=True)
    try:
        driver.get(SEARCH_URL)
        books = extract_books(driver)
    finally:
        driver.quit()
    results = []
    for book in books:
        row = asdict(book)
        row["Format-Year"] = row.pop("Format_Year")
        results.append(row)
    df = pd.DataFrame(results, columns=["Title", "Author", "Format-Year"])
    print(df)
    df.to_csv(CSV_PATH, index=False)
    JSON_PATH.write_text(json.dumps(results, indent=2), encoding="utf-8")

    print(f"Wrote {CSV_PATH}")
    print(f"Wrote {JSON_PATH}")

if __name__ == "__main__":
    main()

