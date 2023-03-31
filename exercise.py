from __future__ import annotations
from abc import ABC, abstractmethod
from random import randint, choice
from datetime import datetime
import os

#------------------------------------------------------------------
# Helpers
#------------------------------------------------------------------

_ALL_EXERCISES = {}


def register_exercise_type(ex_type):
    _ALL_EXERCISES[ex_type.TYPE] = ex_type


def get_all_exercise_types():
    return list(_ALL_EXERCISES.values())


def create_exercise(ty: str, strrepr: str) -> Exercise:
    assert ty in _ALL_EXERCISES
    return _ALL_EXERCISES[ty](strrepr)


def gen_math_int(digits: int, min: int = None, max: int = None) -> int:
    """Get an integer with number of digits for math exercises in the region

    NOTE: Below numbers will never appear since they are too easy to calc

    0, 1 for 1-digit interger
    Any number which is end with 0, i.e. divisible by 10
    All 1 numbers, e.g. 11, 111, etc.
    """
    if digits == 1:
        return randint(2, 9)
    l = 1
    for _ in range(digits - 1):
        l *= 10
    if min is not None and min > l:
        l = min
    h = l * 10 - 1
    if max is not None and max < h:
        h = max

    all_ones = 1
    for _ in range(digits - 1):
        all_ones = all_ones * 10 + 1

    def _is_ok(r: int) -> bool:
        if r % 10 == 0:
            return False
        if r == all_ones:
            return False
        return True

    n = randint(l, h)
    while not _is_ok(n):
        n = randint(l, h)
    return n


#------------------------------------------------------------------
# Exercises
#------------------------------------------------------------------


class Exercise(ABC):
    """Abstract base class for all exercises
    """

    # Every Exercise type should have a static TYPE and register it so
    # that it could be created by factory
    TYPE = "Exercise"

    # Every Exercise type should have a description
    DESC = "Abstract Type for Exercise"

    Correct = 0  # User's answer ins correct
    Invalid = 1  # Invalid answer, e.g. typed by mistake so not a legal int
    Error = 2  # Error answer. e.g. typed an int but not matching the answer

    def __init__(self, strrepr=None) -> None:
        """It should be able to create from nothing or a string repr
        """

    @abstractmethod
    def __str__(self) -> str:
        """It should returns something like 16 x ? = 96 where ? is a placeholder
        to get user input
        """

    @abstractmethod
    def get_repr(self) -> str:
        """The unique representation for the exercise. 
        
        For example, there might be two exercises 16 x ? = 96 and 16 x 6 = ?
        But they are actually the same exercise by the nature, so we hash
        them as 16 x 6 = 96 so consider as the same question for statistics

        The constructor could use repr to create a new Exercise
        """

    @abstractmethod
    def check(self, input: str) -> tuple[int, str | None]:
        """Check user's input vs. answer. The 1st element should be one of
        Correct, Invalid or Error, and second is optional message 
        """


class IntExercise(Exercise):
    """Integer related exercises"""
    TYPE = "IntExercise"

    DESC = "Abstract Type of Exercises Related to Integer Arithmetic"

    def __init__(self, strrepr=None) -> None:
        super().__init__(strrepr)
        self.answer = None

    def check(self, input: str) -> tuple[int, str | None]:
        try:
            x = int(input)
            if x != self.answer:
                return Exercise.Error, f"{x} is Incorrect!"
            else:
                return Exercise.Correct, None
        except:
            return Exercise.Invalid, f"{input} is NOT an integer!"


#------------------------------------------------------------------
# Sessions and Generators
#------------------------------------------------------------------


class ExerciseGen(ABC):
    """Its implementations provides varaious ways to generate new exercises"""
    @abstractmethod
    def get_an_exercise(self) -> Exercise:
        """Generate an exercise"""


class TypeExerciseGen(ExerciseGen):
    """Generate based on a set of exercise types"""
    def __init__(self, types: str | list[str]) -> None:
        self.types = types

    def get_an_exercise(self) -> Exercise:
        ty = choice(self.types) if isinstance(self.types, list) else self.types
        assert ty in _ALL_EXERCISES
        return _ALL_EXERCISES[ty]()


class ReprExerciseGen(ExerciseGen):
    """Generate exercises based on a list of tuples of repr.
    
    This is in particular useful for exercises from the history logs
    """
    def __init__(self, reprs: list[tuple[str, str]], is_random: bool) -> None:
        """
        reprs is something like [("2X2", "16, 18"), ...]
        is_random means whether randomly pick up one from it
        """
        self.reprs = reprs
        self.is_random = is_random
        self.idx = 0  # if we need to sequentially pick up items

    def get_an_exercise(self) -> Exercise:
        if self.is_random:
            ty, strrepr = choice(self.reprs)
        else:
            ty, strrepr = self.reprs[self.idx]
            self.idx += 1
            if self.idx >= len(self.reprs):
                self.idx = 0
        return create_exercise(ty, strrepr)


class ExerciseSession:
    """Record a series of results of exercises"""
    def __init__(self, data_dir: str) -> None:
        """data_dir is the path to store all data files"""
        self.data_dir = data_dir
        self.count = 0
        self.correct = 0
        self.incorrect = 0
        self.items = []
        self.total_time = 0
        self.date = datetime.today().strftime("%Y-%m-%d")

    def finish_an_exercise(self, ex: Exercise, correct: bool, ms_elapsed: int):
        self.count += 1
        self.total_time += ms_elapsed
        if correct:
            self.correct += 1
        else:
            self.incorrect += 1
        self.items.append({
            "type": ex.TYPE,
            "repr": ex.get_repr(),
            "correct": correct,
            "ms_elapsed": ms_elapsed,
            "date": self.date
        })

    def store_results(self) -> None:
        if self.count == 0:
            return
        p = os.path.join(self.data_dir, "_data", "sessions.csv")
        isnew = not os.path.exists(p)
        with open(p, "a") as f:
            if isnew:
                f.write("date,duration_ms,count,correct,incorrect\n")
            f.write(
                f"{self.date},{self.total_time},{self.count},{self.correct},{self.incorrect}\n"
            )

        p = os.path.join(self.data_dir, "_data", "exercises.csv")
        isnew = not os.path.exists(p)
        with open(p, "a") as f:
            if isnew:
                f.write("type,repr,correct,ms_elapsed,date\n")
            for x in self.items:
                f.write(
                    f"{x['type']},{x['repr']},{1 if x['correct'] else 0},{x['ms_elapsed']},{x['date']}\n"
                )


#------------------------------------------------------------------
# Analysis of Exercises Results
#------------------------------------------------------------------

#------------------------------------------------------------------
# Real Exercises
#------------------------------------------------------------------


class TwoXTwoExercise(IntExercise):
    """ a x b = ?  in which a and b are two digits integer
    """

    TYPE = "Int2X2"

    DESC = "A 2-digit integer times another 2-digit integer"

    def __init__(self, strrepr=None) -> None:
        super().__init__(strrepr)
        if strrepr:
            self.a, self.b = [int(x) for x in strrepr.split(",")]
        else:
            self.a = gen_math_int(2)
            self.b = gen_math_int(2)

        self.answer = self.a * self.b

    def __str__(self) -> str:
        return f"{self.a} x {self.b} = ?"

    def get_repr(self) -> str:
        return f"{self.a},{self.b}"


register_exercise_type(TwoXTwoExercise)


class OneXTwoExercise(IntExercise):
    """ a x b = c in which a is 1 digit and b is 2 digit is <39, and if 
    b is above 20, a will be only 2 or 3

    The actual str could be any of the following form: 
    a x b = ?   b x a = ?   a x ? = c  b x ? = c  ? x a = c   ? x b = c
    """
    TYPE = "Int1X2"

    DESC = "A 2-digit integer times a single digit integer"

    def __init__(self, strrepr=None) -> None:
        super().__init__(strrepr)
        if strrepr:
            a, b = [int(x) for x in strrepr.split(",")]
        else:
            b = gen_math_int(2, max=29)
            if b < 20:
                a = gen_math_int(1)
            else:
                a = choice([2, 3])
        c = a * b

        self.a, self.b, self.c = a, b, c

        self.ex_str, self.answer = choice([
            (f"{a} x {b} = ?", c),
            (f"{b} x {a} = ?", c),
            (f"{a} x ? = {c}", b),
            (f"{b} x ? = {c}", a),
            (f"? x {a} = {c}", b),
            (f"? x {b} = {c}", a),
        ])

    def get_repr(self) -> str:
        return f"{self.a},{self.b}"

    def __str__(self) -> str:
        return self.ex_str


register_exercise_type(OneXTwoExercise)