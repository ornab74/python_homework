import functools
import logging
from pathlib import Path
from typing import Any, Callable


LOG_PATH = Path("./decorator.log")


logger = logging.getLogger(__name__ + "_parameter_log")
logger.setLevel(logging.INFO)
logger.propagate = False

if not any(isinstance(handler, logging.FileHandler) for handler in logger.handlers):
    logger.addHandler(logging.FileHandler(LOG_PATH, "a"))


def _format_positional_parameters(args: tuple[Any, ...]) -> str:
    if not args:
        return "none"

    return str(list(args))


def _format_keyword_parameters(kwargs: dict[str, Any]) -> str:
    if not kwargs:
        return "none"

    return str(kwargs)


def logger_decorator(func: Callable) -> Callable:
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)

        logger.log(logging.INFO, f"function: {func.__name__}")
        logger.log(logging.INFO, f"positional parameters: {_format_positional_parameters(args)}")
        logger.log(logging.INFO, f"keyword parameters: {_format_keyword_parameters(kwargs)}")
        logger.log(logging.INFO, f"return: {result}")

        return result

    return wrapper


@logger_decorator
def hello_world():
    print("Hello, World!")


@logger_decorator
def positional_logger(*args):
    return True


@logger_decorator
def keyword_logger(**kwargs):
    return logger_decorator


def main():
    hello_world()
    positional_logger("alpha", "beta", 3)
    keyword_logger(name="Graylan", lesson=3, active=True)


if __name__ == "__main__":
    main()
