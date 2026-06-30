import assignment1 as a1
from decimal import Decimal


def test_hello():
    assert a1.hello() == "Hello"


def test_hello_name():
    assert a1.hello_name("James") == "Hello James"


def test_calc():
    result = a1.calc(5, 6, "multiply")
    assert result.success is True
    assert result.result == Decimal("30")

    result = a1.calc(5, 6, "add")
    assert result.success is True
    assert result.result == Decimal("11")

    result = a1.calc(20, 5, "divide")
    assert result.success is True
    assert result.result == Decimal("4")

    result = a1.calc(14, 2.0, "multiply")
    assert result.success is True
    assert result.result == Decimal("28.0")

    result = a1.calc(12.6, 4.4, "subtract")
    assert result.success is True
    assert result.result == Decimal("8.2")

    result = a1.calc(9, 5, "modulo")
    assert result.success is True
    assert result.result == Decimal("4")

    result = a1.calc(10, 0, "divide")
    assert result.success is False
    assert result.error == "Cannot divide by zero"

    result = a1.calc("first", "second", "multiply")
    assert result.success is False
    assert result.error == "Invalid data was provided."


def test_data_type_conversion():
    result = a1.data_type_conversion("110", "int")
    assert result.success
    assert isinstance(result.value, int)
    assert result.value == 110

    result = a1.data_type_conversion("5.5", "float")
    assert result.success
    assert isinstance(result.value, float)
    assert result.value == 5.5

    result = a1.data_type_conversion(7, "float")
    assert result.success
    assert result.value == 7.0

    result = a1.data_type_conversion(91.1, "str")
    assert result.success
    assert result.value == "91.1"

    result = a1.data_type_conversion("banana", "int")
    assert not result.success


def test_grade():
    assert a1.grade(75, 85, 95) == "B"
    assert a1.grade("three", "blind", "mice") == "Invalid data was provided."


def test_repeat():
    assert a1.repeat("up,", 4) == "up,up,up,up,"


def test_student_scores():
    result = a1.student_scores(
        "mean",
        Tom=75,
        Dick=89,
        Angela=91,
    )

    assert result == Decimal("85")

    result = a1.student_scores(
        "best",
        Tom=75,
        Dick=89,
        Angela=91,
        Frank=50,
    )

    assert result == "Angela"


def test_titleize():
    assert a1.titleize("war and peace") == "War and Peace"
    assert a1.titleize("a separate peace") == "A Separate Peace"
    assert a1.titleize("after on") == "After On"


def test_hangman():
    assert a1.hangman("difficulty", "ic") == "_i__ic____"


def test_pig_latin():
    assert a1.pig_latin("apple") == "appleay"
    assert a1.pig_latin("banana") == "ananabay"
    assert a1.pig_latin("cherry") == "errychay"
    assert a1.pig_latin("quiet") == "ietquay"
    assert a1.pig_latin("square") == "aresquay"
    assert a1.pig_latin("the quick brown fox") == "ethay ickquay ownbray oxfay"