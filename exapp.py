from __future__ import annotations
import os
from time import monotonic

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Static, Input, Label, Button
from textual import events
from textual.message import Message, MessageTarget
from textual.widgets import RadioButton, RadioSet

from exercise import Exercise, TwoXTwoExercise, OneXTwoExercise, TypeExerciseGen, ReprExerciseGen, ExerciseGen, ExerciseSession

# Ensure we are in the correct dir and related dir is ready
FILE_DIR = os.path.dirname(__file__)
os.makedirs(os.path.join(FILE_DIR, "_data"), exist_ok=True)
os.chdir(FILE_DIR)


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


class ExerciseUI(Container):
    DEFAULT_CSS = """

    .content {
        align: center middle;
    }

    #title {
        width: auto;
        content-align: right top;
        height: 5;
    }

    #status {
        width: auto;
        content-align: right top;
        height: 2;
    }

    .incorrect ExerciseWidget {
        border: heavy red;
    }

    .correct ExerciseWidget {
        border: heavy green;
    }

    """

    class Completed(Message):
        def __init__(self, session: ExerciseSession) -> None:
            super().__init__()
            self.session = session

    def __init__(self, gen: ExerciseGen, driving_options: tuple[str, int],
                 *args, **kwargs) -> None:
        """ There are two modes to drive the exercise

         one is by time, e.g. do 5 mins exercises the other is by the number of
         exercises, e.g. do 100 exercises

         So driving_options is something like ("time", 5*60) that means 5min
         or ("count", 100) that means 100 exercises
        """
        self.gen = gen
        self.driving_mode, self.driving_count = driving_options
        assert self.driving_mode in ["time", "count"]
        self.driving_remaining = self.driving_count
        self.session = ExerciseSession(FILE_DIR)

        self.start_time = monotonic()
        super().__init__(*args, **kwargs)

    def compose(self) -> ComposeResult:
        self.ex_container = Container(classes="content")
        with self.ex_container:
            yield Static(
                "Press [bold blue] ctrl + d[/] to [bold yellow]stop[/]",
                id="title")
            self.status = Static(id="status")
            yield self.status

    def new_exercise(self):
        if hasattr(self, "ex"):
            self.ex.remove()
        self.exercise = self.gen.get_an_exercise()
        self.ex = ExerciseWidget(str(self.exercise))
        self.ex_container.mount(self.ex)
        self.start_time = monotonic()

    def on_mount(self):
        if self.driving_mode == "time":
            self.set_interval(1, self.time_tick)
        self.update_status()
        self.new_exercise()

    def time_tick(self):
        self.driving_remaining -= 1
        self.update_status()
        if self.driving_remaining <= 0:
            self.done()

    def update_status(self):
        status = f" [bold green]✓ {self.session.correct}[/]"
        status += f"  [bold red] x {self.session.incorrect}[/]"
        if self.driving_mode == "count":
            remain = str(self.driving_remaining)
        else:
            minutes, seconds = divmod(self.driving_remaining, 60)
            hours, minutes = divmod(minutes, 60)
            remain = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        status += f"      [bold white] Remaining: [bold yellow]{remain}[/]"
        self.status.update(status)

    def done(self):
        self.session.store_results()
        self.post_message(self.Completed(self.session))

    def on_key(self, e: events.Key):
        if e.key == "ctrl+d":
            self.done()
            return
        if e.key != "enter":
            return
        result, msg = self.exercise.check(self.ex.fetch_value(clear=True))
        ms_elapsed = int((monotonic() - self.start_time) * 1000)
        if result != Exercise.Correct:
            self.remove_class("correct")
            self.add_class("incorrect")
            if result == Exercise.Invalid:
                self.start_time = monotonic()
            elif result == Exercise.Error:
                self.session.finish_an_exercise(self.exercise, False,
                                                ms_elapsed)
        else:
            self.remove_class("incorrect")
            self.add_class("correct")
            self.session.finish_an_exercise(self.exercise, True, ms_elapsed)
            self.new_exercise()
            if self.driving_mode == "count":
                self.driving_remaining -= 1
        self.update_status()
        if self.driving_remaining <= 0:
            self.done()


class StartUI(Container):
    DEFAULT_CSS = """
    StartUI {
        layout: vertical;
        align: center middle;
    }
    Horizontal {
        height: 30; 
        width: 100%;
        align: center top;
        content-align: center top;
    }
    Vertical {
        width: auto;
        align: center top;
    }
    .bar {
        width: auto;
        height: 36%;
    }
    .space {
        width: auto;
        height: 10;
    }
    .v1 {
        align: right top;
    }
    .v2 {
        align: center top;
        width: 30;
    }
    .v3 {
        align: left top;
    }
    #go {
        text-style: bold;
        background: royalblue;
        color: white;
    }
    """

    class Start(Message):
        def __init__(self, driver: tuple[str, int], ty: str,
                     source: str) -> None:
            super().__init__()
            self.driver = driver
            self.type = ty
            self.source = source

    DRIVERS = [
        ("3 min", ("time", 3 * 60)),
        ("5 min", ("time", 5 * 60)),
        ("20 exercises", ("count", 20)),
        ("50 exercises", ("count", 50)),
    ]

    TYPES = [
        ("1-digit X 2-digit", OneXTwoExercise),
        ("2-digit X 2-digit", TwoXTwoExercise),
    ]

    SOURCES = [
        ("new", "new"),
        ("review", "review"),
    ]

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def compose(self) -> ComposeResult:
        with Horizontal():
            with Vertical(classes="v1"):
                yield Static(classes="bar")
                yield Label("# Exercises")
                with RadioSet(id="driver"):
                    for idx, x in enumerate(self.DRIVERS):
                        yield RadioButton(x[0], value=idx == 0)
            with Vertical(classes="v2"):
                yield Static(classes="bar")
                yield Label("Type")
                with RadioSet(id="type"):
                    for idx, x in enumerate(self.TYPES):
                        yield RadioButton(x[0], value=idx == 0)
                yield Static(classes="space")
                yield Button("Press Enter to Start", id="go")
            with Vertical(classes="v3"):
                yield Static(classes="bar")
                yield Label("Source")
                with RadioSet(id="source"):
                    for idx, x in enumerate(self.SOURCES):
                        yield RadioButton(x[0], value=idx == 0)

    def on_mount(self):
        self.query_one("#go").focus()

    def on_key(self, e: events.Key) -> None:
        if e.key != "enter":
            return
        self.post_message(
            self.Start(
                self.DRIVERS[self.query_one("#driver").pressed_index][1],
                self.TYPES[self.query_one("#type").pressed_index][1],
                self.SOURCES[self.query_one("#source").pressed_index][1],
            ))


class SummaryUI(Container):
    DEFAULT_CSS = """
    .content {
        align: center middle;
    }

    Static {
        width: auto;
        content-align: left middle;
        height: 2;
    }

    #key {
        display: none;
    }

    """

    class Command(Message):
        def __init__(self, cmd: str) -> None:
            super().__init__()
            self.command = cmd

    def __init__(self, session: ExerciseSession, *args, **kwargs) -> None:
        self.session = session
        super().__init__(*args, **kwargs)

    def compose(self) -> ComposeResult:
        with Container(classes="content"):
            yield Input(id="key")  # a hack way to accept keyboard event
            yield Static(
                f"[bold yellow]Total # Exercises:[/] {self.session.count}")
            yield Static(f"[bold green]  # Correct:[/] {self.session.correct}")
            yield Static(f"[bold red]  # Wrong:[/] {self.session.incorrect}")
            if self.session.count > 0:
                avg = f"{self.session.total_time / self.session.count / 1000:.2f}"
            else:
                avg = "N/A"
            yield Static(f"[bold yellow] Average Time:[/] {avg} seconds")

            yield Static()
            yield Static("Press [bold blue]ENTER[/] to [bold yellow]Do More[/]")
            yield Static(
                "Press [bold blue]ctrl + d[/] to [bold yellow]See Analysis[/]")
            yield Static("Press [bold blue]ctrl + c[/] to [bold yellow]Quit[/]")

    def on_mount(self):
        self.query_one("#key").focus()

    def on_key(self, e: events.Key):
        if e.key == "enter":
            self.post_message(self.Command("do_more"))
        elif e.key == "ctrl+d":
            pass


class MainApp(App):
    DEFAULT_CSS = """
    Screen {
        align: center middle;
    }
    """

    def compose(self) -> ComposeResult:
        self.ui = StartUI()
        yield self.ui

    def on_exercise_ui_completed(self, msg: ExerciseUI.Completed) -> None:
        self.ui.remove()
        self.ui = SummaryUI(msg.session)
        self.mount(self.ui)

    def on_start_ui_start(self, msg: StartUI.Start) -> None:
        self.start_msg = msg
        self.ui.remove()
        gen = None
        if msg.source == "new":
            gen = TypeExerciseGen(msg.type.TYPE)
        self.ui = ExerciseUI(gen, msg.driver)
        self.mount(self.ui)

    def on_summary_ui_command(self, msg: SummaryUI.Command) -> None:
        if msg.command == "do_more":
            self.on_start_ui_start(self.start_msg)

    def on_key(self, e: events.Key):
        return


app = MainApp()
app.run()