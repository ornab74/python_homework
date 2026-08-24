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
OWASP_URL = "https://owasp.org/Top10/2025/0x00_2025-Introduction/"

OUTPUT = Path(__file__).resolve().parent / "owasp_top_10.csv"


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


def main():
    driver = create_driver()

    try:
        # Task 6: Load the OWASP Top 10 page
        driver.get(OWASP_URL)

        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located(
                (By.TAG_NAME, "body")
            )
        )

        time.sleep(2)

        # Task 6:
        # Find links on the page whose visible text begins
        # with an OWASP Top 10 ranking such as A01, A02, etc.
        vulnerability_elements = driver.find_elements(
            By.XPATH,
            "//a["
            "starts-with(normalize-space(.), 'A01:') or "
            "starts-with(normalize-space(.), 'A02:') or "
            "starts-with(normalize-space(.), 'A03:') or "
            "starts-with(normalize-space(.), 'A04:') or "
            "starts-with(normalize-space(.), 'A05:') or "
            "starts-with(normalize-space(.), 'A06:') or "
            "starts-with(normalize-space(.), 'A07:') or "
            "starts-with(normalize-space(.), 'A08:') or "
            "starts-with(normalize-space(.), 'A09:') or "
            "starts-with(normalize-space(.), 'A10:')"
            "]"
        )

        # Task 6: Keep each vulnerability in a dict
        results = []

        for element in vulnerability_elements:
            title = " ".join(element.text.split())
            href = element.get_attribute("href")

            if title and href:
                vulnerability = {
                    "Title": title,
                    "href": href,
                }

                results.append(vulnerability)

            if len(results) == 10:
                break

        # Task 6: Print the list
        print(results)

        # Task 6: Write the list to CSV
        with open(
            OUTPUT,
            "w",
            newline="",
            encoding="utf-8",
        ) as csv_file:

            writer = csv.DictWriter(
                csv_file,
                fieldnames=["Title", "href"],
            )

            writer.writeheader()
            writer.writerows(results)

        print(f"Wrote {OUTPUT}")

    finally:
        driver.quit()


if __name__ == "__main__":
    main()
