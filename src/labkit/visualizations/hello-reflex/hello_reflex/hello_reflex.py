import reflex as rx

class State(rx.State):
    count: int = 0

    @rx.event
    def increment(self):
        self.count += 1


    @rx.event
    def decrement(self):
        self.count -= 1


class TextState(rx.State):
    text: str = "Blured"

    @rx.event
    def update_text(self, new_text: str):
        self.text = new_text


def text_input():
    return rx.vstack(
        rx.heading(State.count, ' ', TextState.text),
        rx.input(
            default_value=TextState.text,
            on_change=TextState.update_text,
        ),
    )


def index():
    return rx.hstack(
        rx.button(
            "Decrement",
            color_scheme='ruby',
            on_click=State.decrement
        ),
        rx.heading(State.count, font_size="2em"),
        rx.button(
            "Increment",
            color_scheme="grass",
            on_click=State.increment,
        ),
        text_input(),
        spacing='4'
    )


app = rx.App()
app.add_page(index)

