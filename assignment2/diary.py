import traceback

def print_exception_details(error):
    print("An exception occurred.")
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

def write_diary():
    try:
        prompt = "What happened today? "
        with open("diary.txt", "a") as diary_file:
            while True:
                entry = input(prompt)
                diary_file.write(entry + "\n")
                if entry == "done for now":
                    break
                prompt = "What else? "
    except Exception as error:
        print_exception_details(error)

if __name__ == "__main__":
    write_diary()