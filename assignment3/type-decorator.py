import functools
from typing import Any, Callable, Type


def type_converter(type_of_output: Type) -> Callable:
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            value = func(*args, **kwargs)
            return type_of_output(value)

        return wrapper

    return decorator


@type_converter(str)
def return_int():
    return 5


@type_converter(int)
def return_string():
    return "not a number"


def main():
    y = return_int()
    print(type(y).__name__)

    try:
        y = return_string()
        print("shouldn't get here!")
    except ValueError:
        print("can't convert that string to an integer!")


if __name__ == "__main__":
    main()
