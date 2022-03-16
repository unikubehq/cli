import asyncio
import sys
from typing import Any, Callable, List

from InquirerPy.prompts import FuzzyPrompt

from unikube.cli.utils import Spinner


class UpdatableFuzzyPrompt(FuzzyPrompt):
    """Based on InquirerPy's FuzzyPrompt.

    Takes an update_function which should return choices.
    The current choices are then replaced by the new ones.
    """

    def __init__(self, update_func: Callable[[], List[str]] = None, **kwargs) -> None:
        super(UpdatableFuzzyPrompt, self).__init__(**kwargs)
        if update_func:
            self._update_func = update_func

    async def _update_choices(self, *args, **kwargs):
        # Call update function to retrieve choices
        # spinner = Spinner("Refreshing...")
        # spinner.start()
        choices = await self._update_func()
        # spinner.stop()
        if not len(choices):
            return
        # keep current choice selection
        # if choice is removed, go to first one
        self.content_control.choices = self.content_control._get_choices(choices, choices[0])
        # internal thing from InqurirerPy - needed to format choice data structure properly
        self.content_control._format_choices()
        # Do the update asynchronously
        self._task = asyncio.create_task(self.content_control._filter_choices(0.01))
        self._task.add_done_callback(self._choice_update_callback)

    def execute(self, raise_keyboard_interrupt: bool = None) -> Any:
        loop = asyncio.new_event_loop()
        prompt = loop.create_task(self.execute_async())
        loop.create_task(self._update_choices())
        loop.run_until_complete(prompt)

    def _choice_update_callback(self, task):
        # Triggers terminal update
        if task.cancelled():
            return
        self.content_control._filtered_choices = task.result()
        self._application.invalidate()
