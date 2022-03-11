import asyncio
from typing import Callable, List

from InquirerPy.prompts import FuzzyPrompt


class UpdatableFuzzyPrompt(FuzzyPrompt):
    """Based on InquirerPy's FuzzyPrompt.

    Takes an update_function which should return choices.
    The current choices are then replaced by the new ones.
    """

    def __init__(self, update_func: Callable[[], List[str]] = None, **kwargs) -> None:
        keybindings = kwargs.get("keybindings", {})
        if update_func:
            keybindings.update(
                {
                    "choice_update": [
                        {"key": "left"},
                    ]
                }
            )
        super(UpdatableFuzzyPrompt, self).__init__(**kwargs)
        if update_func:
            self._update_func = update_func

        def _update_choices(*args, **kwargs):
            # Call update function to retrieve choices
            choices = self._update_func()
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

        # When "choice_update" key combination is triggered
        # run `_update_choices` function.
        if update_func:
            self.kb_func_lookup.update(
                {
                    "choice_update": [{"func": _update_choices}],
                }
            )

    def _choice_update_callback(self, task):
        # Triggers terminal update
        if task.cancelled():
            return
        self.content_control._filtered_choices = task.result()
        self._application.invalidate()
