import asyncio


class StepTimeoutError(asyncio.TimeoutError):
    """
        A timeout Error for Daemon Behaviour Behaviour.step()
    """


class BrainStepTimeoutError(StepTimeoutError):
    """
         timeout Error for Brain receive from Queue.
    """


class BehaviourError(BaseException):
    pass


class AgentError(BaseException):
    pass


class AgentStoppedError(AgentError):
    pass
