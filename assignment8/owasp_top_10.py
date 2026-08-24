from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
import csv
import time

from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


# Source
OWASP_URL = "https://owasp.org/www-project-top-ten/"

# Output path
OUTPUT = Path(__file__).resolve().parent / "owasp_top_10.csv"


# Risk state
@dataclass(slots=True)
class Risk:
    title: str
    href: str


def create_driver() -> webdriver.Chrome:
    # Browser state
    options = webdriver.ChromeOptions()

    # Runtime options
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")

    # Start driver
    return webdriver.Chrome(
        service=ChromeService(ChromeDriverManager().install()),
        options=options,
    )


def extract_risks(driver: webdriver.Chrome) -> list[Risk]:
    # Wait for page
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "body"))
    )

    time.sleep(1)

    # Search paths
    xpath_candidates = [
        "//a[contains(@href, 'Top_10') and contains(., 'A0')]",
        "//a[contains(@href, 'A01') or contains(@href, 'A02') or contains(@href, 'A03') or contains(@href, 'A04') or contains(@href, 'A05') or contains(@href, 'A06') or contains(@href, 'A07') or contains(@href, 'A08') or contains(@href, 'A09') or contains(@href, 'A10')]",
        "//a[contains(., 'Broken Access Control') or contains(., 'Cryptographic Failures') or contains(., 'Injection')]",
    ]

    # Track unique links
    seen: set[str] = set()
    risks: list[Risk] = []

    # Probe paths
    for xpath in xpath_candidates:
        for anchor in driver.find_elements(By.XPATH, xpath):
            title = " ".join(anchor.text.strip().split())
            href = anchor.get_attribute("href") or ""

            # Reject weak result
            if not title or not href or href in seen:
                continue

            # Capture result
            seen.add(href)
            risks.append(Risk(title=title, href=href))

        # Limit state
        if len(risks) >= 10:
            break

    return risks[:10]


def write_csv(risks: list[Risk]) -> None:
    # Write output
    with OUTPUT.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["title", "href"],
        )

        writer.writeheader()
        writer.writerows(asdict(risk) for risk in risks)


def main() -> None:
    # Open browser
    driver = create_driver()

    try:
        driver.get(OWASP_URL)
        risks = extract_risks(driver)
    finally:
        # Close browser
        driver.quit()

    # Print results
    for risk in risks:
        print(asdict(risk))

    # Save results
    write_csv(risks)

    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    # Execute
    main()

