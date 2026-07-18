import csv
from pathlib import Path


EMPLOYEES_PATH = Path("../csv/employees.csv")


def read_employee_rows(path: Path = EMPLOYEES_PATH) -> list[list[str]]:
    with open(path, "r", newline="") as file:
        return list(csv.reader(file))


def employee_names(rows: list[list[str]]) -> list[str]:
    fields = rows[0]
    first_name_index = fields.index("first_name")
    last_name_index = fields.index("last_name")

    return [
        f"{row[first_name_index]} {row[last_name_index]}"
        for row in rows[1:]
    ]


def names_containing_e(names: list[str]) -> list[str]:
    return [
        name
        for name in names
        if "e" in name.lower()
    ]


def main():
    rows = read_employee_rows()
    names = employee_names(rows)
    e_names = names_containing_e(names)

    print(names)
    print(e_names)


if __name__ == "__main__":
    main()
