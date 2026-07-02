from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Callable, Iterable
import re


INVALID_DATA = "Invalid data was provided."


@dataclass(frozen=True, slots=True)
class CalcResult:
    success: bool
    result: Decimal | None = None
    error: str | None = None


@dataclass(frozen=True, slots=True)
class ConversionResult:
    success: bool
    value: Any = None
    error: str | None = None


@dataclass(frozen=True, slots=True)
class Operation:
    name: str
    function: Callable[[Decimal, Decimal], Decimal]
    block_zero: bool = False


@dataclass(frozen=True, slots=True)
class GradeBand:
    minimum: Decimal
    letter: str


@dataclass(frozen=True, slots=True)
class GradeReport:
    average: Decimal
    letter: str


@dataclass(frozen=True, slots=True)
class RepeatRequest:
    text: str
    count: int


@dataclass(frozen=True, slots=True)
class StudentReport:
    best_student: str
    mean_score: Decimal
class DecimalTools:
    @staticmethod
    def from_value(value: Any, *, allow_string: bool = True) -> Decimal:
        if isinstance(value, bool):
            raise ValueError(f"{value!r} is not numeric")

        if isinstance(value, str) and not allow_string:
            raise ValueError(f"{value!r} is not numeric")

        try:
            number = Decimal(str(value))
        except (InvalidOperation, ValueError):
            raise ValueError(f"{value!r} is not numeric")

        if not number.is_finite():
            raise ValueError(f"{value!r} is not finite")

        return number

    @staticmethod
    def bounded_score(value: Any) -> Decimal:
        number = DecimalTools.from_value(value, allow_string=False)

        if not Decimal("0") <= number <= Decimal("100"):
            raise ValueError(f"{value!r} is outside the valid score range")

        return number

    @staticmethod
    def whole_number(value: Any) -> int:
        number = DecimalTools.from_value(value, allow_string=True)

        if number != number.to_integral_value():
            raise ValueError(f"{value!r} isn't a whole number")

        return int(number)


def hello() -> str:
    return "Hello!"


def greet(name: str) -> str:
    return f"Hello, {name}!"

class Calculator:
    def __init__(self):
        self.operations: dict[str, Operation] = {}

    def register(self, operation: Operation):
        self.operations[operation.name] = operation

    def calc(self, num1: Any, num2: Any, operation_name: str) -> CalcResult:
        operation = self.operations.get(operation_name)

        if operation is None:
            return CalcResult(
                success=False,
                error=f"Invalid operation: {operation_name}"
            )

        try:
            left = DecimalTools.from_value(num1)
            right = DecimalTools.from_value(num2)

            if operation.block_zero and right == 0:
                return CalcResult(
                    success=False,
                    error="Cannot divide by zero"
                )

            return CalcResult(
                success=True,
                result=operation.function(left, right)
            )

        except ValueError:
            return CalcResult(
                success=False,
                error=INVALID_DATA
            )

        except TypeError:
            return CalcResult(
                success=False,
                error=INVALID_DATA
            )

        except Exception as error:
            return CalcResult(
                success=False,
                error=f"Unexpected error: {error}"
            )


def build_calculator() -> Calculator:
    calculator = Calculator()

    calculator.register(Operation("add", lambda a, b: a + b))
    calculator.register(Operation("subtract", lambda a, b: a - b))
    calculator.register(Operation("multiply", lambda a, b: a * b))
    calculator.register(Operation("divide", lambda a, b: a / b, block_zero=True))
    calculator.register(Operation("modulo", lambda a, b: a % b, block_zero=True))
    calculator.register(Operation("int_divide", lambda a, b: a // b, block_zero=True))
    calculator.register(Operation("power", lambda a, b: a ** b))

    return calculator


calculator = build_calculator()


def calc(num1, num2, operation):
    return calculator.calc(num1, num2, operation)


class ConversionEngine:
    @staticmethod
    def to_int(value: Any) -> int:
        return DecimalTools.whole_number(value)

    @staticmethod
    def to_float(value: Any) -> float:
        if isinstance(value, bool):
            raise ValueError

        number = float(value)

        if number in (float("inf"), float("-inf")) or number != number:
            raise ValueError

        return number

    @staticmethod
    def to_str(value: Any) -> str:
        return str(value)


CONVERTERS: dict[str, Callable[[Any], Any]] = {
    "float": ConversionEngine.to_float,
    "str": ConversionEngine.to_str,
    "string": ConversionEngine.to_str,
    "int": ConversionEngine.to_int,
    "integer": ConversionEngine.to_int,
}


def data_type_conversion(value: Any, target_type: str) -> ConversionResult:
    if not isinstance(target_type, str):
        return ConversionResult(
            success=False,
            error=INVALID_DATA
        )

    key = target_type.strip().lower()
    converter = CONVERTERS.get(key)

    if converter is None:
        return ConversionResult(
            success=False,
            error=f"Invalid type {target_type!r}."
        )

    try:
        return ConversionResult(
            success=True,
            value=converter(value)
        )

    except (ValueError, TypeError) as error:
        return ConversionResult(
            success=False,
            error=f"Can't convert {value!r} to {key}: {error}"
        )


class GradeEngine:
    SCALE = (
        GradeBand(Decimal("90"), "A"),
        GradeBand(Decimal("80"), "B"),
        GradeBand(Decimal("70"), "C"),
        GradeBand(Decimal("60"), "D"),
        GradeBand(Decimal("0"), "F"),
    )

    @classmethod
    def parse_scores(cls, scores: Iterable[Any]) -> tuple[Decimal, ...]:
        parsed = tuple(DecimalTools.bounded_score(score) for score in scores)

        if not parsed:
            raise ValueError

        return parsed

    @staticmethod
    def average(scores: tuple[Decimal, ...]) -> Decimal:
        return sum(scores, Decimal("0")) / Decimal(len(scores))

    @classmethod
    def letter_for_average(cls, average: Decimal) -> str:
        for band in cls.SCALE:
            if average >= band.minimum:
                return band.letter

        raise ValueError

    @classmethod
    def evaluate(cls, *scores: Any) -> GradeReport:
        parsed = cls.parse_scores(scores)
        average = cls.average(parsed)

        return GradeReport(
            average=average,
            letter=cls.letter_for_average(average)
        )


def grade(*scores):
    try:
        return GradeEngine.evaluate(*scores).letter

    except ValueError:
        return INVALID_DATA


class RepeatEngine:
    MAX_REPEAT = 10_000

    @classmethod
    def build_request(cls, text: Any, count: Any) -> RepeatRequest:
        if not isinstance(text, str):
            raise ValueError

        if isinstance(count, bool) or not isinstance(count, int):
            raise ValueError

        if not 0 <= count <= cls.MAX_REPEAT:
            raise ValueError

        return RepeatRequest(text, count)

    @classmethod
    def repeat(cls, text: Any, count: Any) -> str:
        request = cls.build_request(text, count)
        output = []

        for _ in range(request.count):
            output.append(request.text)

        return "".join(output)


def repeat(text, count):
    try:
        return RepeatEngine.repeat(text, count)

    except ValueError:
        return INVALID_DATA


class StudentScoreEngine:
    REQUEST_ALIASES = {
        "best": "best_student",
        "best_student": "best_student",
        "top": "best_student",
        "top_student": "best_student",
        "mean": "mean_score",
        "mean_score": "mean_score",
        "average": "mean_score",
        "avg": "mean_score",
    }

    @classmethod
    def normalize_request(cls, request: Any) -> str:
        if not isinstance(request, str):
            raise ValueError

        key = request.strip().lower().replace(" ", "_")
        normalized = cls.REQUEST_ALIASES.get(key)

        if normalized is None:
            raise ValueError

        return normalized

    @staticmethod
    def parse_scores(scores: dict[str, Any]) -> dict[str, Decimal]:
        if not scores:
            raise ValueError

        parsed = {}

        for student, score in scores.items():
            if not isinstance(student, str) or not student.strip():
                raise ValueError

            parsed[student] = DecimalTools.bounded_score(score)

        return parsed

    @staticmethod
    def best_student(scores: dict[str, Decimal]) -> str:
        best_score = max(scores.values())
        winners = [
            student
            for student, score in scores.items()
            if score == best_score
        ]

        return sorted(winners)[0]

    @staticmethod
    def mean_score(scores: dict[str, Decimal]) -> Decimal:
        return sum(scores.values(), Decimal("0")) / Decimal(len(scores))

    @classmethod
    def evaluate(cls, **scores: Any) -> StudentReport:
        parsed = cls.parse_scores(scores)

        return StudentReport(
            best_student=cls.best_student(parsed),
            mean_score=cls.mean_score(parsed)
        )

    @classmethod
    def request(cls, request: Any, **scores: Any):
        normalized = cls.normalize_request(request)
        report = cls.evaluate(**scores)

        if normalized == "best_student":
            return report.best_student

        if normalized == "mean_score":
            return report.mean_score

        raise ValueError


def student_scores(request: str, **scores):
    try:
        return StudentScoreEngine.request(request, **scores)

    except ValueError:
        return INVALID_DATA


SMALL_WORDS = {
    "a",
    "on",
    "an",
    "the",
    "of",
    "and",
    "is",
    "in",
}


class TitleEngine:
    WORD_PATTERN = re.compile(r"([^A-Za-z]*)([A-Za-z]+(?:'[A-Za-z]+)?)([^A-Za-z]*)")

    @classmethod
    def split_word(cls, word: str) -> tuple[str, str, str]:
        match = cls.WORD_PATTERN.fullmatch(word)

        if match is None:
            return "", word, ""

        return match.group(1), match.group(2), match.group(3)

    @staticmethod
    def capitalize_core(core: str) -> str:
        lowered = core.lower()
        return lowered[:1].upper() + lowered[1:]

    @classmethod
    def titleize_word(cls, word: str, index: int, last_index: int) -> str:
        prefix, core, suffix = cls.split_word(word)

        if not core:
            return word

        lowered = core.lower()

        if 0 < index < last_index and lowered in SMALL_WORDS:
            fixed = lowered
        else:
            fixed = cls.capitalize_core(lowered)

        return f"{prefix}{fixed}{suffix}"

    @classmethod
    def titleize(cls, title: Any):
        if not isinstance(title, str):
            return INVALID_DATA

        words = title.split()

        if not words:
            return ""

        last_index = len(words) - 1

        return " ".join(
            cls.titleize_word(word, index, last_index)
            for index, word in enumerate(words)
        )


def titleize(title):
    return TitleEngine.titleize(title)


class HangmanEngine:
    HIDDEN = "_"

    @staticmethod
    def validate_secret(secret_word: Any) -> str:
        if not isinstance(secret_word, str) or not secret_word:
            raise ValueError

        return secret_word

    @staticmethod
    def validate_guesses(guessed_letters: Any) -> set[str]:
        if not isinstance(guessed_letters, str):
            raise ValueError

        return {
            letter.lower()
            for letter in guessed_letters
            if letter.isalpha()
        }

    @classmethod
    def reveal(cls, secret_word: Any, guessed_letters: Any) -> str:
        secret = cls.validate_secret(secret_word)
        guesses = cls.validate_guesses(guessed_letters)
        revealed = []

        for char in secret:
            if not char.isalpha():
                revealed.append(char)
            elif char.lower() in guesses:
                revealed.append(char)
            else:
                revealed.append(cls.HIDDEN)

        return "".join(revealed)


def hangman(secret_word, guessed_letters):
    try:
        return HangmanEngine.reveal(secret_word, guessed_letters)

    except ValueError:
        return INVALID_DATA


VOWELS = {"a", "e", "i", "o", "u"}


class PigLatinEngine:
    TOKEN_PATTERN = re.compile(r"[A-Za-z]+(?:'[A-Za-z]+)?|[^A-Za-z]+")

    @staticmethod
    def is_word(token: str) -> bool:
        return token.replace("'", "").isalpha()

    @staticmethod
    def preserve_case(original: str, translated: str) -> str:
        if original.isupper():
            return translated.upper()

        if original[:1].isupper():
            return translated.capitalize()

        return translated

    @staticmethod
    def cluster_end(word: str) -> int:
        index = 0

        while index < len(word):
            if word[index] in VOWELS:
                break

            if word[index] == "q" and index + 1 < len(word) and word[index + 1] == "u":
                index += 2
                continue

            index += 1

        return index

    @classmethod
    def translate_word(cls, word: str) -> str:
        lowered = word.lower()

        if not lowered:
            return word

        if lowered[0] in VOWELS:
            translated = f"{lowered}ay"
            return cls.preserve_case(word, translated)

        split_index = cls.cluster_end(lowered)

        if split_index >= len(lowered):
            translated = f"{lowered}ay"
        else:
            translated = f"{lowered[split_index:]}{lowered[:split_index]}ay"

        return cls.preserve_case(word, translated)

    @classmethod
    def translate(cls, text: Any):
        if not isinstance(text, str):
            return INVALID_DATA

        tokens = cls.TOKEN_PATTERN.findall(text)

        return "".join(
            cls.translate_word(token) if cls.is_word(token) else token
            for token in tokens
        )


def pig_latin(text):
    return PigLatinEngine.translate(text)

def run_greeting_examples():
    print(hello())
    print(greet("Graylan"))


def run_calculator_examples():
    print(calc(10, 5, "add"))
    print(calc(10, 5, "subtract"))
    print(calc(10, 5, "multiply"))
    print(calc(10, 5, "divide"))
    print(calc(10, 3, "modulo"))
    print(calc(10, 3, "int_divide"))
    print(calc(2, 8, "power"))
    print(calc(10, 0, "divide"))
    print(calc("hello", "world", "multiply"))
    print(calc(10, 5, "pizza"))


def run_conversion_examples():
    print(data_type_conversion("42", "int"))
    print(data_type_conversion("42.0", "int"))
    print(data_type_conversion("42.5", "int"))
    print(data_type_conversion("3.14", "float"))
    print(data_type_conversion(99, "str"))
    print(data_type_conversion("pizza", "float"))
    print(data_type_conversion("hello", "int"))
    print(data_type_conversion("100", "integer"))
    print(data_type_conversion("100", "string"))
    print(data_type_conversion("100", "bool"))


def run_grade_examples():
    print(grade(100, 100, 90))
    print(grade(80, 79, 81))
    print(grade(70, 75, 72))
    print(grade(60, 59, 61))
    print(grade(40, 50, 55))
    print(grade())
    print(grade(True, 90))
    print(grade("90", 100))
    print(grade(101, 90))
    print(grade(-1, 90))


def run_repeat_examples():
    print(repeat("Hi", 3))
    print(repeat("Python", 2))
    print(repeat("A", 5))
    print(repeat("Hello", 0))
    print(repeat(123, 3))
    print(repeat("Hi", "3"))
    print(repeat("Hi", -1))
    print(repeat("Hi", True))
    print(repeat("Hi", 10001))


def run_student_scores_examples():
    print(student_scores("best_student", Graylan=100, Alex=88, Sam=92))
    print(student_scores("mean_score", Graylan=100, Alex=88, Sam=92))
    print(student_scores("best", Mia=76, Zoe=99, Jay=99))
    print(student_scores("average", Mia=76, Zoe=99, Jay=99))
    print(student_scores("best_student"))
    print(student_scores("mean_score", Graylan=True, Alex=90))
    print(student_scores("mean_score", Graylan="100", Alex=90))
    print(student_scores("pizza", Graylan=100, Alex=90))


def run_titleize_examples():
    print(titleize("along the road we travel"))
    print(titleize("can we write this correctly"))
    print(titleize("stop and smell the roses"))
    print(titleize("the bridge on the riverside"))
    print(titleize("organize your program"))
    print(titleize(""))
    print(titleize(123))


def run_hangman_examples():
    print(hangman("alphabet", "ab"))
    print(hangman("python", "po"))
    print(hangman("Graylan", "ga"))
    print(hangman("ice-cream", "ic"))
    print(hangman("", "abc"))
    print(hangman(123, "abc"))
    print(hangman("alphabet", 123))


def run_pig_latin_examples():
    print(pig_latin("apple"))
    print(pig_latin("banana"))
    print(pig_latin("queen"))
    print(pig_latin("square"))
    print(pig_latin("Hello, world!"))
    print(pig_latin("Quick quiet queen."))
    print(pig_latin(123))


def main():
    run_greeting_examples()
    run_calculator_examples()
    run_conversion_examples()
    run_grade_examples()
    run_repeat_examples()
    run_student_scores_examples()
    run_titleize_examples()
    run_hangman_examples()
    run_pig_latin_examples()


if __name__ == "__main__":
    main()