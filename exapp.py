from __future__ import annotations
from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Static, Input
from textual import events

from exercise import Exercise, OneXTwoExercise


class ExerciseWidget(Container):
    """Render an exercise string as a Widget

    The exercise is a string like 16 x ? = 80  or 16 x 6 = ?

    The ? will be converted into an input asking for user input

    """
    DEFAULT_CSS = """
    ExerciseWidget {
        layout: horizontal;
        align: center middle;
        border: heavy white;
        width: auto;
        height: auto;
        padding: 2 10;
    }

    ExerciseWidget Static {
        content-align: center middle;
        width: auto;
        height: 3;
        margin: 0;
        padding: 0;
    }

    ExerciseWidget Input {
        content-align: center middle;
        width: 10;
        height: 3;
        margin: 0;
        padding: 0 1;
        color: orange;
    }
    """

    def __init__(self, exercise: str, *args, **kwargs) -> None:
        self.ex_exercise = exercise.split("?")
        assert len(self.ex_exercise) == 2  # should have one and only one ?
        super().__init__(*args, **kwargs)

    def compose(self) -> ComposeResult:
        if self.ex_exercise[0]:
            yield Static(self.ex_exercise[0])
        self.input = Input()
        yield self.input
        if self.ex_exercise[1]:
            yield Static(self.ex_exercise[1])

    def on_mount(self):
        self.input.styles.border = "none", "orange"
        self.input.focus()

    def fetch_value(self, clear=False) -> str:
        result = self.input.value
        if clear:
            self.input.value = ""
        return result


class ExerciseUI(App):
    DEFAULT_CSS = """
    Screen {
        align: center middle;
    }

    .content {
        align: center middle;
    }

    #message {
        width: auto;
        content-align: center top;
        height: 3;
    }

    """

    def compose(self) -> ComposeResult:
        self.ex_container = Container(classes="content")
        with self.ex_container:
            self.message = Static(id="message")
            yield self.message

    def new_exercise(self):
        if hasattr(self, "ex"):
            self.ex.remove()
        self.exercise = OneXTwoExercise()
        self.ex = ExerciseWidget(str(self.exercise))
        self.ex_container.mount(self.ex)

    def on_mount(self):
        self.new_exercise()

    def on_key(self, e: events.Key):
        if e.key != "enter":
            return
        result, msg = self.exercise.check(self.ex.fetch_value(clear=True))
        if msg:
            self.message.update(f"[bold red]{msg}[/]")
        else:
            self.message.update(f"[bold green]Correct![/]")
            self.new_exercise()


# there are two modes to drive the exercise
# one is by time, e.g. do 5 mins exercises
# the other is by the number of exercises, e.g. do 100 exercises

app = ExerciseUI()
app.run()