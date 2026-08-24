from pathlib import Path
import csv
import re
import time

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


# Task 6: Use the exact page assigned in the instructions.
OWASP_URL = "https://owasp.org/www-project-top-ten/"

OUTPUT = Path(__file__).resolve().parent / "owasp_top_10.csv"
FIELDNAMES = ["Vulnerability Title", "href"]

# The project page now links to the current release instead of embedding the
# ten entries. This XPath selects that official link from the first paragraph.
CURRENT_RELEASE_XPATH = (
    "//h1[contains(normalize-space(.), 'OWASP Top Ten')]"
    "/following::p[1]//a[contains(@href, '/Top10/20')]"
)

# On an OWASP release page, each risk is an anchor inside a list item.
VULNERABILITY_XPATH = (
    "//li/a["
    "starts-with(normalize-space(.), 'A') and "
    "contains(normalize-space(.), ':20')"
    "]"
)

VULNERABILITY_TITLE_PATTERN = re.compile(
    r"^A(0[1-9]|10):20\d{2}\s*[-\u2013\u2014]\s*\S"
)


def create_driver():
    # Task 6: Create Selenium driver
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
    return " ".join((value or "").split())


def vulnerability_rank(title):
    """Return the A01-A10 rank for a valid OWASP vulnerability title."""
    match = VULNERABILITY_TITLE_PATTERN.match(title)
    if not match:
        return None

    return int(match.group(1))


def collect_vulnerabilities(elements):
    """Build the requested dictionaries and remove duplicate DOM links."""
    vulnerabilities_by_rank = {}

    for element in elements:
        title = normalize_text(element.text)
        href = element.get_attribute("href")
        rank = vulnerability_rank(title)

        if rank is None or not href or rank in vulnerabilities_by_rank:
            continue

        vulnerabilities_by_rank[rank] = {
            "Vulnerability Title": title,
            "href": href,
        }

    return [
        vulnerabilities_by_rank[rank]
        for rank in range(1, 11)
        if rank in vulnerabilities_by_rank
    ]


def find_vulnerability_elements(driver):
    """Find risks on the assigned page or its official current-release link."""
    elements = driver.find_elements(By.XPATH, VULNERABILITY_XPATH)

    if len(collect_vulnerabilities(elements)) == 10:
        return elements

    # OWASP changed the project page: it currently links to the release page.
    # Start from the assigned URL, read that link from its DOM, then scrape the
    # ten list items on the official release page rather than hard-coding a
    # different OWASP URL.
    release_link = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located(
            (By.XPATH, CURRENT_RELEASE_XPATH)
        )
    )
    release_url = release_link.get_attribute("href")

    if not release_url:
        raise RuntimeError("OWASP current-release link has no href value")

    driver.get(release_url)

    return WebDriverWait(driver, 20).until(
        EC.presence_of_all_elements_located(
            (By.XPATH, VULNERABILITY_XPATH)
        )
    )


def main():
    driver = create_driver()

    try:
        # Task 6: Load the exact OWASP project page from the assignment.
        driver.get(OWASP_URL)

        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        time.sleep(2)

        vulnerability_elements = find_vulnerability_elements(driver)
        results = collect_vulnerabilities(vulnerability_elements)

        if len(results) != 10:
            raise RuntimeError(
                f"Expected 10 OWASP vulnerabilities, found {len(results)}"
            )

        # Task 6: Print the list
        print(results)

        # Task 6: Write the list of dicts to CSV.
        with open(
            OUTPUT,
            "w",
            newline="",
            encoding="utf-8",
        ) as csv_file:
            writer = csv.DictWriter(
                csv_file,
                fieldnames=FIELDNAMES,
            )

            writer.writeheader()
            writer.writerows(results)

        print(f"Wrote {OUTPUT}")

    finally:
        driver.quit()


if __name__ == "__main__":
    main()
