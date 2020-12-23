import asyncio


class StepTimeoutError(asyncio.TimeoutError):
    """
        A timeout Error for Daemon Behaviour Behaviour.step()
    """


class BrainStepTimeoutError(StepTimeoutError):
    """
         timeout Error for Brain receive from Queue.
    """
