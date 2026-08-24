from pathlib import Path
import csv
import time

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


# Task 6: OWASP Top 10 page
OWASP_URL = "https://owasp.org/www-project-top-ten/"

OUTPUT = Path(__file__).resolve().parent / "owasp_top_10.csv"


def create_driver():
    # Task 6: Create Selenium driver
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
        # Task 6: Load OWASP page
        driver.get(OWASP_URL)

        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located(
                (By.TAG_NAME, "body")
            )
        )

        time.sleep(2)

        # Task 6:
        # Use XPath to directly find links for the 2025 Top 10 risks.
        risk_elements = driver.find_elements(
            By.XPATH,
            "//a["
            "contains(@href, '/Top10/2025/A01_') or "
            "contains(@href, '/Top10/2025/A02_') or "
            "contains(@href, '/Top10/2025/A03_') or "
            "contains(@href, '/Top10/2025/A04_') or "
            "contains(@href, '/Top10/2025/A05_') or "
            "contains(@href, '/Top10/2025/A06_') or "
            "contains(@href, '/Top10/2025/A07_') or "
            "contains(@href, '/Top10/2025/A08_') or "
            "contains(@href, '/Top10/2025/A09_') or "
            "contains(@href, '/Top10/2025/A10_')"
            "]"
        )

        # Task 6: Store vulnerability dictionaries
        risks = []
        seen = set()

        for element in risk_elements:
            title = " ".join(element.text.split())
            href = element.get_attribute("href")

            # Prevent duplicate links
            if not title or not href or href in seen:
                continue

            seen.add(href)

            risk = {
                "title": title,
                "href": href,
            }

            risks.append(risk)

            # We only need the Top 10
            if len(risks) == 10:
                break

        # Task 6: Print list
        print(risks)

        # Task 6: Write results to CSV
        with open(
            OUTPUT,
            "w",
            newline="",
            encoding="utf-8",
        ) as csv_file:

            writer = csv.DictWriter(
                csv_file,
                fieldnames=["title", "href"],
            )

            writer.writeheader()
            writer.writerows(risks)

        print(f"Wrote {OUTPUT}")

    finally:
        driver.quit()


if __name__ == "__main__":
    main()

