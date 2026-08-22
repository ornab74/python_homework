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

OWASP_URL = "https://owasp.org/www-project-top-ten/"
OUTPUT = Path(__file__).resolve().parent / "owasp_top_10.csv"

@dataclass(slots=True)

class Risk:
    title: str
    href: str

def create_driver() -> webdriver.Chrome:
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")

    return webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)

def extract_risks(driver: webdriver.Chrome) -> list[Risk]:
    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, "body")))
    time.sleep(1)
    xpath_candidates = [
        "//a[contains(@href, 'Top_10') and contains(., 'A0')]",
        "//a[contains(@href, 'A01') or contains(@href, 'A02') or contains(@href, 'A03') or contains(@href, 'A04') or contains(@href, 'A05') or contains(@href, 'A06') or contains(@href, 'A07') or contains(@href, 'A08') or contains(@href, 'A09') or contains(@href, 'A10')]",
        "//a[contains(., 'Broken Access Control') or contains(., 'Cryptographic Failures') or contains(., 'Injection')]",
    ]

    seen: set[str] = set()
    risks: list[Risk] = []
    for xpath in xpath_candidates:
        for anchor in driver.find_elements(By.XPATH, xpath):
            title = " ".join(anchor.text.strip().split())
            href = anchor.get_attribute("href") or ""
            if not title or not href or href in seen:
                continue
            seen.add(href)
            risks.append(Risk(title=title, href=href))

        if len(risks) >= 10:
            break
    return risks[:10]

def write_csv(risks: list[Risk]) -> None:
    with OUTPUT.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["title", "href"])
        writer.writeheader()
        writer.writerows(asdict(risk) for risk in risks)

def main() -> None:
    driver = create_driver()
    try:
        driver.get(OWASP_URL)
        risks = extract_risks(driver)
    finally:
        driver.quit()
    for risk in risks:
        print(asdict(risk))
    write_csv(risks)
    print(f"Wrote {OUTPUT}")

if __name__ == "__main__":
    main()

