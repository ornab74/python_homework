from pathlib import Path
import csv
import random
import re
import time

from selenium import webdriver
from selenium.common.exceptions import (
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager


# Task 6: start with the exact page named in the assignment.
ASSIGNED_OWASP_URL = "https://owasp.org/www-project-top-ten/"

# Task 6: write the CSV inside the assignment8 folder.
OUTPUT_DIR = Path(__file__).resolve().parent
OUTPUT_PATH = OUTPUT_DIR / "owasp_top_10.csv"

FIELDNAMES = [
    "Vulnerability Title",
    "href",
]

MAX_ATTEMPTS = 4
WAIT_SECONDS = 25
BACKOFF_SECONDS = 2
MIN_JITTER = 2.5
MAX_JITTER = 5.5


# The assigned OWASP project page links to the current Top Ten release.
# This XPath finds that release link without hard-coding the ten risks.
RELEASE_LINK_XPATH = (
    "//a["
    "contains(@href, '/Top10/2025/') and "
    "contains(normalize-space(.), 'OWASP Top Ten 2025')"
    "]"
)


# Task 6 / lesson XPath approach:
# start from a useful heading and navigate through the DOM structure.
TOP_TEN_HEADING_XPATH = (
    "//*[self::h1 or self::h2 or self::h3]"
    "[contains(normalize-space(.), 'OWASP Top 10') or "
    "contains(normalize-space(.), 'OWASP Top Ten')]"
)


# After XPath locates the relevant section, validate that a collected link
# represents one of the A01-A10 vulnerability entries.
TITLE_PATTERN = re.compile(
    r"^A(0[1-9]|10):2025\b"
)


def create_driver():
    # Task 6: create a Selenium Chrome driver using webdriver_manager,
    # following the same setup shown in the lesson.
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
    # Return a normalized string with whitespace condensed down to single spaces
    # and leading/trailing whitespace removed.
    return " ".join(
        (value or "").split()
    )


def jitter_sleep(
    label,
    base=0.0,
):
    # Sleep for a random duration to avoid sending requests too rapidly.
    delay = (
        base
        + random.uniform(
            MIN_JITTER,
            MAX_JITTER,
        )
    )

    print(
        f"{label}: "
        f"{delay:.2f} seconds"
    )

    time.sleep(delay)


def rank_from_title(title):
    # Return the integer rank 1-10 from titles such as
    # A01:2025 or A10:2025.
    match = TITLE_PATTERN.match(
        title
    )

    if not match:
        return None

    return int(
        match.group(1)
    )


def load_with_retry(
    driver,
    url,
    description,
):
    # Load pages with bounded exponential backoff and randomized jitter.
    last_error = None

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
                lambda browser:
                browser.find_element(
                    By.TAG_NAME,
                    "body",
                )
            )

            jitter_sleep(
                "Render delay"
            )

            return

        except (
            TimeoutException,
            WebDriverException,
        ) as error:
            last_error = error

            if attempt == MAX_ATTEMPTS:
                break

            base = (
                BACKOFF_SECONDS
                * (2 ** (attempt - 1))
            )

            jitter_sleep(
                f"{description} was not ready; "
                "backoff before retry",
                base=base,
            )

    raise RuntimeError(
        f"Unable to load {description} "
        f"after {MAX_ATTEMPTS} attempts."
    ) from last_error


def find_release_url(driver):
    # Task 6: use XPath to locate the current release link
    # from the exact page supplied in the assignment.
    links = WebDriverWait(
        driver,
        WAIT_SECONDS,
    ).until(
        lambda browser:
        browser.find_elements(
            By.XPATH,
            RELEASE_LINK_XPATH,
        )
        or False
    )

    for link in links:
        href = link.get_attribute(
            "href"
        )

        if href:
            return href

    raise RuntimeError(
        "The OWASP project page did not expose a release href."
    )


def candidate_section_containers(driver):
    # Use the XPath parent/sibling technique shown in the lesson.
    #
    # Start from a heading related to the OWASP Top Ten section,
    # move up to its parent, then inspect nearby sibling containers.
    headings = driver.find_elements(
        By.XPATH,
        TOP_TEN_HEADING_XPATH,
    )

    containers = []

    for heading in headings:
        # XPath '..' moves up to the parent element.
        parent = heading.find_element(
            By.XPATH,
            "..",
        )

        containers.append(
            parent
        )

        # XPath following-sibling axis moves across to related containers.
        siblings = parent.find_elements(
            By.XPATH,
            "following-sibling::*",
        )

        containers.extend(
            siblings[:4]
        )

        # Some page layouts may put the heading and risk list
        # inside a larger parent wrapper.
        try:
            grandparent = parent.find_element(
                By.XPATH,
                "..",
            )

            containers.append(
                grandparent
            )

        except WebDriverException:
            pass

    # Structural fallback if the section layout changes slightly.
    containers.extend(
        driver.find_elements(
            By.CSS_SELECTOR,
            "main",
        )
    )

    return containers


def collect_top_ten_from_dom(driver):
    # Task 6: accumulate vulnerability dictionaries in a list.
    #
    # XPath is used to navigate to the relevant DOM section first.
    # Once inside that section, collect its links and keep only A01-A10.
    by_rank = {}

    for container in candidate_section_containers(
        driver
    ):
        link_elements = container.find_elements(
            By.CSS_SELECTOR,
            "a",
        )

        for link in link_elements:
            title = normalize_text(
                link.text
            )

            href = link.get_attribute(
                "href"
            )

            rank = rank_from_title(
                title
            )

            if rank is None:
                continue

            if not href:
                continue

            if rank in by_rank:
                continue

            # Task 6: each vulnerability is stored in a dict
            # containing its title and href.
            vulnerability = {
                "Vulnerability Title": title,
                "href": href,
            }

            by_rank[rank] = vulnerability

        if len(by_rank) == 10:
            break

    # Task 6: accumulate the dict objects in a list in A01-A10 order.
    results = []

    for rank in range(
        1,
        11,
    ):
        if rank in by_rank:
            results.append(
                by_rank[rank]
            )

    return results


def wait_for_top_ten(driver):
    # Wait until XPath DOM navigation exposes all ten vulnerability links.
    def all_ten_loaded(browser):
        results = collect_top_ten_from_dom(
            browser
        )

        if len(results) == 10:
            return results

        return False

    return WebDriverWait(
        driver,
        WAIT_SECONDS,
    ).until(
        all_ten_loaded
    )


def main():
    driver = create_driver()

    try:
        # Task 6: Selenium reads the exact page supplied by the assignment.
        load_with_retry(
            driver,
            ASSIGNED_OWASP_URL,
            "the assigned OWASP Top Ten page",
        )

        # Task 6: use XPath to find the release link.
        release_url = find_release_url(
            driver
        )

        print(
            "Discovered release URL "
            f"from assigned page: {release_url}"
        )

        # Small pause before following the second page.
        jitter_sleep(
            "Small delay before following "
            "OWASP release link"
        )

        load_with_retry(
            driver,
            release_url,
            "the OWASP Top Ten 2025 release page",
        )

        # Task 6:
        # XPath parent/sibling navigation identifies the relevant section.
        # The vulnerability titles and href values are then stored in dicts.
        try:
            results = wait_for_top_ten(
                driver
            )

        except TimeoutException as error:
            raise RuntimeError(
                "The OWASP release page loaded, "
                "but XPath DOM navigation did not "
                "expose all 10 vulnerability links."
            ) from error

        # Task 6: print the list to verify the data.
        print(results)

        # Task 6: write the list of dicts to owasp_top_10.csv.
        with OUTPUT_PATH.open(
            "w",
            newline="",
            encoding="utf-8",
        ) as csv_file:
            writer = csv.DictWriter(
                csv_file,
                fieldnames=FIELDNAMES,
            )

            writer.writeheader()
            writer.writerows(
                results
            )

        print(
            f"Wrote {OUTPUT_PATH}"
        )

    finally:
        driver.quit()


if __name__ == "__main__":
    # Run the main function.
    main()
