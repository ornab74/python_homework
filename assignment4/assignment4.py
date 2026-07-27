from pathlib import Path
import json
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
EMPLOYEES_CSV = BASE_DIR / "employees.csv"
ADDITIONAL_JSON = BASE_DIR / "additional_employees.json"
DIRTY_CSV = BASE_DIR / "dirty_data.csv"


def _print_section(title: str) -> None:
    print("\n" + "=" * 72)
    print(title)
    print("=" * 72)


def _ensure_dirty_data() -> None:
    if DIRTY_CSV.exists():
        return

    fallback_dirty = pd.DataFrame(
        {
            "Name": [" Alice ", "Bob", "Bob", " charlie", "Dana ", "Eva", "Frank"],
            "Age": ["25", "30", "30", "unknown", "41", None, "35"],
            "Salary": ["70000", "80000", "80000", "unknown", "n/a", "90000", "95000"],
            "Hire Date": [
                "2020-01-15",
                "2019-03-10",
                "2019-03-10",
                "not a date",
                "2021-06-01",
                "",
                "2022-07-22",
            ],
            "Department": [
                " engineering ",
                "sales",
                "sales",
                "Engineering",
                "hr ",
                "finance",
                "FINANCE ",
            ],
        }
    )

    fallback_dirty.to_csv(DIRTY_CSV, index=False)


def _to_mixed_datetime(series: pd.Series) -> pd.Series:
    try:
        return pd.to_datetime(series, format="mixed", errors="coerce")
    except TypeError:
        return series.apply(lambda value: pd.to_datetime(value, errors="coerce"))


employee_seed = {
    "Name": ["Alice", "Bob", "Charlie"],
    "Age": [25, 30, 35],
    "City": ["New York", "Los Angeles", "Chicago"],
}

task1_data_frame = pd.DataFrame(employee_seed)

_print_section("Task 1A: base DataFrame")
print(task1_data_frame)

task1_with_salary = task1_data_frame.copy()
task1_with_salary["Salary"] = [70000, 80000, 90000]

_print_section("Task 1B: DataFrame with Salary")
print(task1_with_salary)

task1_older = task1_with_salary.copy()
task1_older["Age"] = task1_older["Age"] + 1

_print_section("Task 1C: DataFrame with Age incremented")
print(task1_older)

task1_older.to_csv(EMPLOYEES_CSV, index=False)

_print_section(f"Task 1D: wrote {EMPLOYEES_CSV.name}")
print(EMPLOYEES_CSV.read_text())

task2_employees = pd.read_csv(EMPLOYEES_CSV)

_print_section("Task 2A: loaded employees.csv")
print(task2_employees)

additional_employees = [
    {"Name": "Eve", "Age": 28, "City": "Miami", "Salary": 60000},
    {"Name": "Frank", "Age": 40, "City": "Seattle", "Salary": 95000},
]

ADDITIONAL_JSON.write_text(json.dumps(additional_employees, indent=2), encoding="utf-8")

json_employees = pd.read_json(ADDITIONAL_JSON)

_print_section("Task 2B: loaded additional_employees.json")
print(json_employees)

more_employees = pd.concat([task2_employees, json_employees], ignore_index=True)

_print_section("Task 2C: combined DataFrame")
print(more_employees)

first_three = more_employees.head(3)
last_two = more_employees.tail(2)
employee_shape = more_employees.shape

_print_section("Task 3A: first_three")
print(first_three)

_print_section("Task 3B: last_two")
print(last_two)

_print_section("Task 3C: employee_shape")
print(employee_shape)

_print_section("Task 3D: more_employees.info()")
more_employees.info()

_ensure_dirty_data()

dirty_data = pd.read_csv(DIRTY_CSV)

_print_section("Task 4A: dirty_data")
print(dirty_data)

clean_data = dirty_data.copy()
clean_data = clean_data.drop_duplicates().reset_index(drop=True)

_print_section("Task 4B: duplicates removed")
print(clean_data)

clean_data["Age"] = pd.to_numeric(clean_data["Age"], errors="coerce")

_print_section("Task 4C: Age converted to numeric")
print(clean_data)

clean_data["Salary"] = (
    clean_data["Salary"]
    .astype("string")
    .str.strip()
    .str.lower()
    .replace(
        {
            "unknown": pd.NA,
            "n/a": pd.NA,
            "nan": pd.NA,
            "": pd.NA,
        }
    )
)

clean_data["Salary"] = pd.to_numeric(clean_data["Salary"], errors="coerce")

_print_section("Task 4D: Salary converted to numeric")
print(clean_data)

clean_data["Age"] = clean_data["Age"].fillna(clean_data["Age"].mean())
clean_data["Salary"] = clean_data["Salary"].fillna(clean_data["Salary"].median())

_print_section("Task 4E: missing numeric values filled")
print(clean_data)

clean_data["Hire Date"] = _to_mixed_datetime(clean_data["Hire Date"])

_print_section("Task 4F: Hire Date converted to datetime")
print(clean_data)

clean_data["Name"] = clean_data["Name"].astype("string").str.strip().str.upper()
clean_data["Department"] = clean_data["Department"].astype("string").str.strip().str.upper()

_print_section("Task 4G: text standardized")
print(clean_data)