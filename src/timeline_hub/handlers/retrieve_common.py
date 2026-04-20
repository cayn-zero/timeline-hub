from enum import Enum


class StepOutcome(Enum):
    """Outcome of one retrieval navigation step.

    `SHOWN` means the step handled navigation, either by rendering its menu or
    by advancing through auto-select. `SKIP_BACK` means backward resolution
    should continue to the next higher candidate.
    """

    SHOWN = 'shown'
    SKIP_BACK = 'skip_back'
