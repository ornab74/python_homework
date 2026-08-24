from pathlib import Path
import json
import random
import re
import time
from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit

import pandas as pd
from selenium import webdriver
from selenium.common.exceptions import (
    StaleElementReferenceException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


SEARCH_URL = (
    "https://durhamcounty.bibliocommons.com/v2/search"
    "?query=learning%20spanish&searchType=smart"
)

# Task 4: write the output files inside the assignment8 folder.
OUTPUT_DIR = Path(__file__).resolve().parent
CSV_PATH = OUTPUT_DIR / "get_books.csv"
JSON_PATH = OUTPUT_DIR / "get_books.json"

MAX_ATTEMPTS = 4
WAIT_SECONDS = 25
BACKOFF_SECONDS = 2
MIN_PAGE_DELAY = 2.5
MAX_PAGE_DELAY = 5.5

# Task 2 / Task 3: selectors taken from the inspected result DOM.
RESULT_SELECTOR = "li.row.cp-search-result-item"
TITLE_SELECTOR = "h3.cp-title span.title-content"
AUTHOR_LINK_SELECTOR = "span.cp-author-link a.author-link"
AUTHOR_LINK_FALLBACK_SELECTOR = "a.author-link"
AUTHOR_CONTAINER_SELECTOR = "span.cp-author-link"
FORMAT_YEAR_CONTAINER_SELECTOR = "div.cp-format-info"
FORMAT_YEAR_SELECTOR = "span.display-info-primary"

# the live BiblioCommons pager uses labels such as "Go to page 2", not a
# literal Next link. discover those links from the page rather than assuming
# how many result pages exist.
PAGE_LINK_XPATH = (
    "//a["
    "starts-with(@aria-label, 'Go to page ') or "
    "contains(@href, 'page=')"
    "]"
)


def create_driver():
    # Task 3: create the Selenium Chrome driver using webdriver_manager,
    # as shown in the lesson and required by the assignment rubric.
    options = webdriver.ChromeOptions()

    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    return webdriver.Chrome(
        service=ChromeService(
            ChromeDriverManager().install()
        ),
        options=options,
    )


def normalize_text(value):
    # return a normalized string with whitespace collapsed to single spaces
    # and leading/trailing whitespace removed.
    return " ".join((value or "").split())


def jitter_sleep(label="Pause"):
    # sleep for a random duration between MIN_PAGE_DELAY and MAX_PAGE_DELAY
    # seconds, printing the label and duration.
    delay = random.uniform(
        MIN_PAGE_DELAY,
        MAX_PAGE_DELAY,
    )
    print(f"{label}: {delay:.2f} seconds")
    time.sleep(delay)


def first_text(parent, selectors):
    # return the first non-empty normalized text from the parent element
    # matching any of the CSS selectors
    for selector in selectors:
        for element in parent.find_elements(
            By.CSS_SELECTOR,
            selector,
        ):
            text = normalize_text(
                element.text
            )

            if text:
                return text

    return ""


def extract_authors(item):

    # extract the author(s) from the item element
    author_elements = item.find_elements(
        By.CSS_SELECTOR,
        AUTHOR_LINK_SELECTOR,
    )

    if not author_elements:
        author_elements = item.find_elements(
            By.CSS_SELECTOR,
            AUTHOR_LINK_FALLBACK_SELECTOR,
        )

    raw_authors = [
        element.text
        for element in author_elements
    ]

    if not any(
        normalize_text(author)
        for author in raw_authors
    ):
        author_containers = item.find_elements(
            By.CSS_SELECTOR,
            AUTHOR_CONTAINER_SELECTOR,
        )

        raw_authors = [
            element.text
            for element in author_containers
        ]

    authors = []
    seen = set()

    for raw_author in raw_authors:
        author = normalize_text(
            raw_author
        )

        author = re.sub(
            r"^by\s+",
            "",
            author,
            flags=re.IGNORECASE,
        )

        author = author.strip(
            " ;\u2022"
        )

        key = author.casefold()

        if author and key not in seen:
            authors.append(author)
            seen.add(key)

    # Task 3: multiple authors are joined with a semicolon.
    return "; ".join(authors)


def extract_book(item):

    # extract the title, author, and year from the item element
    title = first_text(
        item,
        [
            TITLE_SELECTOR,
            "h3.cp-title a",
            "h3.cp-title",
        ],
    )

    author_text = extract_authors(
        item
    )

    format_year = ""

    format_containers = item.find_elements(
        By.CSS_SELECTOR,
        FORMAT_YEAR_CONTAINER_SELECTOR,
    )

    if format_containers:
        # Task 3: find the span inside the format/year div.
        format_year = first_text(
            format_containers[0],
            [
                FORMAT_YEAR_SELECTOR,
                "span.display-info",
            ],
        )

    # Task 3: required dictionary keys.
    return {
        "Title": title,
        "Author": author_text,
        "Format-Year": format_year,
    }


def book_key(book):
    return (
        book["Title"].casefold(),
        book["Author"].casefold(),
        book["Format-Year"].casefold(),
    )


def load_url_with_retry(
    driver,
    url,
    description,
):
    last_error = None

    # load with retry and backoff
    for attempt in range(
        1,
        MAX_ATTEMPTS + 1,
    ):
        try:
            print(
                f"Loading {description} "
                f"(attempt {attempt}/{MAX_ATTEMPTS})"
            )

            driver.get(url)

            WebDriverWait(
                driver,
                WAIT_SECONDS,
            ).until(
                EC.presence_of_element_located(
                    (
                        By.CSS_SELECTOR,
                        RESULT_SELECTOR,
                    )
                )
            )

            return

        except (
            TimeoutException,
            WebDriverException,
        ) as error:
            last_error = error

            if attempt == MAX_ATTEMPTS:
                break

            delay = (
                BACKOFF_SECONDS
                * (2 ** (attempt - 1))
                + random.uniform(
                    0.25,
                    1.25,
                )
            )

            print(
                f"{description} was not ready; "
                f"retrying in {delay:.2f} seconds..."
            )

            time.sleep(delay)

    raise RuntimeError(
        f"Unable to load {description} "
        f"after {MAX_ATTEMPTS} attempts."
    ) from last_error


def collect_current_page(driver):

    # collect rendered cards on the current results page.

    page_books = {}
    unchanged_rounds = 0
    last_dom_count = 0

    driver.execute_script(
        "window.scrollTo(0, 0);"
    )

    time.sleep(1)

    for _ in range(40):
        # Task 3: find all result li elements using the inspected classes.
        items = driver.find_elements(
            By.CSS_SELECTOR,
            RESULT_SELECTOR,
        )

        for item in items:
            try:
                book = extract_book(
                    item
                )
            except StaleElementReferenceException:
                continue

            if book["Title"]:
                page_books.setdefault(
                    book_key(book),
                    book,
                )

        dom_count = len(items)

        print(
            f"Current page: "
            f"{dom_count} result elements in DOM; "
            f"{len(page_books)} unique books collected"
        )

        if dom_count > last_dom_count:
            unchanged_rounds = 0
            last_dom_count = dom_count
        else:
            unchanged_rounds += 1

        if items:
            try:
                driver.execute_script(
                    "arguments[0].scrollIntoView("
                    "{block: 'end'}"
                    ");",
                    items[-1],
                )
            except StaleElementReferenceException:
                continue

        # give the site's renderer time to append the next card batch.
        time.sleep(1.5)

        if len(page_books) >= 20:
            break

        if unchanged_rounds >= 5:
            break

    return list(
        page_books.values()
    )


def page_number_from_href(href):
    if not href:
        return None

    query = parse_qs(
        urlsplit(href).query
    )

    try:
        return int(
            query.get(
                "page",
                [None],
            )[0]
        )

    except (
        TypeError,
        ValueError,
    ):
        return None


def discover_page_urls(driver):
    # discover numbered pagination URLs currently advertised by the page
    pages = {}

    for link in driver.find_elements(
        By.XPATH,
        PAGE_LINK_XPATH,
    ):
        href = link.get_attribute(
            "href"
        )

        page_number = page_number_from_href(
            href
        )

        if (
            href
            and page_number
            and page_number >= 2
        ):
            pages[page_number] = href

    return pages


def build_page_url(page_number):
    # preserve the assigned search query while changing only its page number
    parts = urlsplit(
        SEARCH_URL
    )

    query = parse_qs(
        parts.query
    )

    query["page"] = [
        str(page_number)
    ]

    return urlunsplit(
        (
            parts.scheme,
            parts.netloc,
            parts.path,
            urlencode(
                query,
                doseq=True,
            ),
            parts.fragment,
        )
    )


def collect_all_pages(driver):
    # optional extra-credit: collect every advertised search-results page
    all_books = {}
    page_number = 1

    while True:
        print(
            f"\nCollecting Durham "
            f"results page {page_number}"
        )

        page_books = collect_current_page(
            driver
        )

        for book in page_books:
            all_books.setdefault(
                book_key(book),
                book,
            )

        print(
            f"Page {page_number}: "
            f"{len(page_books)} results; "
            f"total unique: "
            f"{len(all_books)}"
        )

        advertised_pages = discover_page_urls(
            driver
        )

        next_page = (
            page_number + 1
        )

        # prefer the URL actually advertised by the site's pagination...
        # if the pager only shows a window of page numbers, construct the
        # immediately following URL using the same query shape and verify
        # it by loading it.
        next_url = advertised_pages.get(
            next_page
        )

        if (
            next_url is None
            and any(
                number > page_number
                for number
                in advertised_pages
            )
        ):
            next_url = build_page_url(
                next_page
            )

        if next_url is None:
            print(
                "No later numbered page advertised; "
                "pagination complete."
            )
            break

        jitter_sleep(
            f"small delay before requesting "
            f"Durham page {next_page}"
        )

        try:
            load_url_with_retry(
                driver,
                next_url,
                f"Durham results page {next_page}",
            )

        except RuntimeError:
            print(
                f"Page {next_page} "
                "could not be loaded; "
                "stopping pagination."
            )
            break

        page_number = next_page

    return list(
        all_books.values()
    )


def main():
    driver = create_driver()

    try:
        # Task 3: load the assigned search URL.
        load_url_with_retry(
            driver,
            SEARCH_URL,
            "Durham search",
        )

        # Task 3: required empty results list.
        results = []

        # Required first-page scraping plus the optional all-pages enhancement.
        for book in collect_all_pages(
            driver
        ):
            # Task 3: append one dict per result.
            results.append(book)

        print(
            f"\nFound {len(results)} "
            "total unique search results"
        )

        # Task 3: create and print DataFrame.
        df = pd.DataFrame(
            results,
            columns=[
                "Title",
                "Author",
                "Format-Year",
            ],
        )

        print(df)

        # Task 4: write CSV inside the assignment8 folder.
        df.to_csv(
            CSV_PATH,
            index=False,
        )

        # Task 4: write results list as JSON inside assignment8.
        with JSON_PATH.open(
            "w",
            encoding="utf-8",
        ) as json_file:
            json.dump(
                results,
                json_file,
                indent=2,
                ensure_ascii=False,
            )

        print(
            f"Wrote {CSV_PATH}"
        )

        print(
            f"Wrote {JSON_PATH}"
        )

    finally:
        driver.quit()


if __name__ == "__main__":
    main()
