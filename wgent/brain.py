"""
    Control the integration between Agent and Behaviours.
    WgentBehavioursTable = NewType("WgentBehavioursTable", Mapping)
    behaviours: WgentBehavioursTable = {

    }
"""
import asyncio
import queue
from concurrent.futures import Future
from concurrent.futures.thread import ThreadPoolExecutor
from typing import List, Any, Dict, Tuple, Optional

from wgent.behaviours import InternalBehaviour, Behaviour
from wgent.acl import ACLMessage
from wgent.base_types import TaskPiece
from wgent.exceptions import BrainStepTimeoutError
from wgent.memory import MemoryHandler
from wgent.utility import logger, start_task


class BrainBehaviour(InternalBehaviour):
    def __init__(self, agent):
        """This method initializes the Behaviour class with an agent instance

            :param agent: agent instance that will execute the behaviours
            established by the protocol

        """
        super(BrainBehaviour, self).__init__(agent)
        # Default thread pool
        self._tasks_pool = ThreadPoolExecutor(
            max_workers=self.agent.config_handler.read().pool_size, thread_name_prefix='brain_')
        self._running_tasks: Dict[str, Future] = {}

    def execute(self, message: ACLMessage):
        """
            Receive message to update self.
        """

    def step(self, timeout: float):
        """
            Just like a iterable step and it should not blocked.
        """
        try:
            task_piece: Tuple[int, TaskPiece] = self.agent.memory_handler.wait_and_get(
                self.agent.memory_pieces_queue, timeout=timeout)
            # create a task in thread or process pool.
            self._running_tasks = start_task(self._running_tasks, self._tasks_pool, self._dispatch_behaviour,
                                             task_piece)
        except queue.Empty:
            raise BrainStepTimeoutError

    async def run(self, timeout: float = 0.1, sleep_time: Optional[int] = None):
        """
            It is the same as Function--On start
        """
        # If sleep_time is None that default value is timeout.
        if sleep_time is None:
            sleep_time = timeout
        # Start the loop event.
        while True:
            try:
                self.step(timeout)
            except asyncio.CancelledError:
                # TODO:Do something here when a daemon process cancelled.
                pass
            except BrainStepTimeoutError:
                logger.info(f"Brain not receive anything in {sleep_time} second...Waiting")
                await asyncio.sleep(sleep_time)

    async def on_start(self, daemon_tasks: List[Behaviour]):
        """
            on_start
        """

        # Start brain event and the other behaviour.
        await asyncio.gather(
            self.run(),  # Brain Wait for 1 second.
            *[b.run() for b in daemon_tasks]
        )

    # -----------------Task--------------------------
    def _dispatch_behaviour(self, task_piece: TaskPiece):
        """
            Dispatch the behaviour to execute the ACLMessage
        """
        if not isinstance(task_piece, TaskPiece):
            raise ValueError("It should be a Tuple(int, TaskPiece) object in Queue")
        executors: List[str] = task_piece.executors
        cur_behaviour_names: Dict[str, Behaviour] = {b.__class__.__name__: b for b in self.agent.behaviours}
        if executors is None:
            # all behaviours
            executors = list(cur_behaviour_names.keys())

        for behaviour in executors:
            # Check it whether in behaviours
            if behaviour in cur_behaviour_names.keys():
                cur_behaviour_names[behaviour].execute(task_piece.memory_piece.content)
            else:
                logger.exception(f"Behaviour:{behaviour} not exist in agent.behaviours.")
