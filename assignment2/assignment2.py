import csv
import os
import traceback
from datetime import datetime
from pathlib import Path
import custom_module

BASE_DIR = Path(__file__).resolve().parent
CSV_DIR = BASE_DIR.parent / "csv"
EMPLOYEES_FILE = CSV_DIR / "employees.csv"
MINUTES1_FILE = CSV_DIR / "minutes1.csv"
MINUTES2_FILE = CSV_DIR / "minutes2.csv"
OUTPUT_MINUTES_FILE = BASE_DIR / "minutes.csv"

def print_exception_details(error):
    trace_back = traceback.extract_tb(error.__traceback__)
    stack_trace = []

    for trace in trace_back:
        stack_trace.append(
            f"File : {trace[0]} , Line : {trace[1]}, Func.Name : {trace[2]}, Message : {trace[3]}"
        )

    print(f"Exception type: {type(error).__name__}")

    message = str(error)
    if message:
        print(f"Exception message: {message}")
    print(f"Stack trace: {stack_trace}")

def read_csv_as_dict(file_path, *, tuple_rows=False):
    data = {}
    rows = []

    try:
        with open(file_path, "r", newline="") as file:
            reader = csv.reader(file)

            for row_number, row in enumerate(reader):
                if row_number == 0:
                    data["fields"] = row
                else:
                    rows.append(tuple(row) if tuple_rows else row)

        data["rows"] = rows
        return data

    except Exception as error:
        print_exception_details(error)
        raise

def read_employees():
    return read_csv_as_dict(EMPLOYEES_FILE)

employees = read_employees()
print(employees)

def column_index(column_name):
    return employees["fields"].index(column_name)

employee_id_column = column_index("employee_id")
print(employee_id_column)

def first_name(row_number):
    first_name_column = column_index("first_name")
    return employees["rows"][row_number][first_name_column]
print(first_name(0))

def employee_find(employee_id):
    def employee_match(row):
        return int(row[employee_id_column]) == employee_id

    matches = list(filter(employee_match, employees["rows"]))
    return matches
print(employee_find(int(employees["rows"][0][employee_id_column])))

def employee_find_2(employee_id):
    matches = list(
        filter(
            lambda row: int(row[employee_id_column]) == employee_id,
            employees["rows"],
        )
    )
    return matches
print(employee_find_2(int(employees["rows"][0][employee_id_column])))

def sort_by_last_name():
    last_name_column = column_index("last_name")
    employees["rows"].sort(key=lambda row: row[last_name_column])
    return employees["rows"]
print(sort_by_last_name())
print(employees)

def employee_dict(row):
    employee = {}

    for field, value in zip(employees["fields"], row):
        if field != "employee_id":
            employee[field] = value

    return employee

print(employee_dict(employees["rows"][0]))

def all_employees_dict():
    all_employees = {}

    for row in employees["rows"]:
        employee_id = row[employee_id_column]
        all_employees[employee_id] = employee_dict(row)

    return all_employees
print(all_employees_dict())

def get_this_value():
    return os.getenv("THISVALUE")
print(get_this_value())

def set_that_secret(new_secret):
    custom_module.set_secret(new_secret)

set_that_secret("open sesame")
print(custom_module.secret)

def read_minutes():
    minutes1 = read_csv_as_dict(MINUTES1_FILE, tuple_rows=True)
    minutes2 = read_csv_as_dict(MINUTES2_FILE, tuple_rows=True)
    return minutes1, minutes2

minutes1, minutes2 = read_minutes()
print(minutes1)
print(minutes2)

def create_minutes_set():
    minutes1_set = set(minutes1["rows"])
    minutes2_set = set(minutes2["rows"])
    return minutes1_set.union(minutes2_set)

minutes_set = create_minutes_set()
print(minutes_set)

def create_minutes_list():
    raw_minutes_list = list(minutes_set)
    converted_minutes_list = list(
        map(
            lambda row: (row[0], datetime.strptime(row[1], "%B %d, %Y")),
            raw_minutes_list,
        )
    )
    return converted_minutes_list

minutes_list = create_minutes_list()
print(minutes_list)


def write_sorted_list():
    minutes_list.sort(key=lambda row: row[1])

    converted_minutes = list(
        map(
            lambda row: (row[0], datetime.strftime(row[1], "%B %d, %Y")),
            minutes_list,
        )
    )

    with open(OUTPUT_MINUTES_FILE, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(minutes1["fields"])
        writer.writerows(converted_minutes)

    return converted_minutes

sorted_minutes = write_sorted_list()
print(sorted_minutes)