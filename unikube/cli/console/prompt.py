import asyncio
from threading import Thread
from typing import Any, Callable, List

from InquirerPy.prompts import FuzzyPrompt


class UpdatableFuzzyPrompt(FuzzyPrompt):
    """Based on InquirerPy's FuzzyPrompt.

    Takes an update_function which should return choices.
    The current choices are then replaced by the new ones.
    """

    def __init__(self, update_func: Callable[[], List[str]] = None, **kwargs) -> None:
        super(UpdatableFuzzyPrompt, self).__init__(**kwargs)
        if update_func:
            self._update_func = update_func

    def _update_choices(self, loop):
        # Call update function to retrieve choices
        choices = self._update_func()
        if not len(choices):
            return
        # keep current choice selection
        # if choice is removed, go to first one
        loop.create_task(self._update_display(choices))

    async def _update_display(self, choices):
        self.content_control.choices = self.content_control._get_choices(
            choices, choices[self.content_control.selected_choice_index]
        )
        # internal thing from InqurirerPy - needed to format choice data structure properly
        self.content_control._format_choices()
        # Do the update asynchronously
        choices = await self.content_control._filter_choices(0.01)
        self.content_control._filtered_choices = choices
        self._application.renderer.erase()
        self._application.invalidate()

    def execute(self, raise_keyboard_interrupt: bool = None) -> Any:
        loop = asyncio.new_event_loop()
        if hasattr(self, "_update_func"):
            thread = Thread(target=self._update_choices, args=[loop])
            thread.start()

        prompt = loop.create_task(self.execute_async())
        answer = loop.run_until_complete(prompt)
        return answer
