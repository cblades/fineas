import threading
from collections import deque
from typing import Union, List

import wrapt


class TransitionException(Exception):
    def __init__(self, msg, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.msg = msg

    def __str__(self):
        return self.msg


class FSMManager:
    """Defines a decorator-based finite state machine manager."""

    def transition(self,
                   source: Union[str, List[str]], dest: str,
                   error_state=None, failed_state=None, reraise_error=True):
        """Defines a transition from one or more source states to a destination state.

        When the decorated method is called, first state machine will validate that the object's
        current state is one of the values in source.  Then, state machine will call the decorated
        method, optionally passing a fail_transition callable if the method accepts it.  If the
        decorated method doesn't 1) raise an exception or 2) call fail_transition, the object's
        state will be updated to be dest.

        Args:
            source: One or more states from which this transition can happen.
            dest: The state this transition is to.
            error_state: If decorated method raises an error, transition to this state.
            failed_state: If decorated method calls fail_transition, transition to this state.
            reraise_error: If decorated method raises an exception, re-raise that exception.
        """
        source = self._listify(source)

        @wrapt.decorator
        def wrap(wrapped, instance, args, kwargs):
            with wrapt.synchronized(instance):
                if instance.state not in source:
                    raise TransitionException(
                        f'Wrong state for transition.  '
                        f'Expected ({self.__format_transition(source, wrapped.__name__, dest)}), '
                        f'but was {self.__format_transition(instance.state, wrapped.__name__, dest)}')
                try:
                    failed = False

                    def _fail():
                        nonlocal failed
                        failed = True

                    try:
                        returnable = wrapped(*args, fail_transition=_fail, **kwargs)
                    except TypeError as t:
                        returnable = wrapped(*args, **kwargs)

                    if failed and failed_state:
                        self._do_transition(instance, f'{wrapped.__name__}!Failed', failed_state)

                    else:
                        self._do_transition(instance, wrapped.__name__, dest)
                    return returnable
                except Exception as e:
                    if error_state:
                        self._do_transition(instance, f'{wrapped.__name__}!Error', error_state)
                    if reraise_error:
                        raise e

        return wrap

    def _do_transition(self, instance: any, transition: str, dest: str):
        """Transitions the objects state and appends the transition to the object's history.

        Args:
            instance: the object being transitioned (current state will be taken from instance.state
            transition: the name of the transition being performed.
            dest: the destination state.
        """
        old_state = instance.state
        instance.state = dest
        if instance.history is not None:
            instance.history.append(
                self.__format_transition(old_state, transition, dest))

    @staticmethod
    def _listify(value):
        """Turn value into a list if it isn't already one."""
        return value if isinstance(value, (list, tuple)) else [value]

    @staticmethod
    def __format_transition(source: Union[str, List[str]], transition: str, dest: str):
        """Pretty-print a state transition."""
        return f'({" OR ".join(FSMManager._listify(source))})--[{transition}]->({dest})'

    def __call__(self, initial_state: str, store_history=False, max_history=100):
        """Turn all instances of a class into state machines.

        Required to use @state_machine.transition() decorator.

        Args:
            initial_state: the initial state of the each instance of this type.
            store_history: Flag to enable storing a log of state transitions.
            max_history: The maximum number of history items to store (default 100)
        """
        @wrapt.decorator
        def wrap(clazz, instance, args, kwargs):
            old_init = clazz.__init__

            def new_init(self, *args, **kwargs):
                self.state = initial_state
                self.history = \
                    deque(
                        [FSMManager.__format_transition('_', '_initial', initial_state)],
                        maxlen=max_history) if store_history else None
                old_init(self, *args, **kwargs)

            clazz.__init__ = new_init
            return clazz(*args, **kwargs)

        return wrap
