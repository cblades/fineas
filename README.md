# Fineas

A simple, thread-safe, decorator-based, transition-focused Finite State Machine implementation.

Possible Use Cases:
- Configuration management from multiple sources.
- Keeping track of state during complex system startup.
- Tracking state while parsing.

```python
from fineas import state_machine


@state_machine(initial_state='new', store_history=True)
class TestMachine:
    def __init__(self):
        self.config = None

    @state_machine.transition(
        source=['new', 'invalid_configuration'],
        dest='configured',
        error_state='invalid_configuration')
    def got_config(self, config):
        # validate config
        self.config = config

    @state_machine.transition(source='configured', dest='scheduled')
    def ready(self):
        pass

    @state_machine.transition(
        source='scheduled',
        dest='scheduled',
        error_state='canceled',
        failed_state='retry')
    def run(self, fail_transition):
        # do work
        status = self._do_work()

        if not status:
            fail_transition()

    @state_machine.transition(
        source='retry',
        dest='run',
        error_state='canceled',
        failed_state='too_many_failures'
    )
    def try_again(self, times, fail_transition):
        for i in range(times):
            if self._do_work():
                return
        fail_transition()

    @state_machine.transition(
        source=['retry', 'too_many_failures'],
        dest='cancelled'
    )
    def abandon(self):
        pass

    @state_machine.transition(
        source='too_many_failures',
        dest='configured'
    )
    def reconfigure(self, config):
        self.config = config

    def _do_work(self):
        pass


t = TestMachine()
t.got_config(None)
t.ready()
t.run()
t.try_again(3)
t.abandon()


print(t.history)

print(t.state)
```

## Quickstart
1) Decorate a class with `@fineas.state_machine(initial_state='new')`.  You must pass a value for 
   `initial_state`.
2) Define a method that implements the work required to transition form one or more source states
   to a single destination state.  Decorate that method with 
   `@fineas.transition(source='new', dest='ready')`.
3)  That's it!  Each instance of your decorated class is its own state machine.  You may check its
current state with its `state` attribute, and, if you've enabled `record_history`, you can access
    its transition history with its `history` attribute.

## Overview
To turn each instance of a class into a state machine, simply decorate it with 
`@fineas.state_machine()`.  You must pass an `initial_state` value to `@fineas.state_machine()`.
This will be the state every instance of your type starts in.  You can also enable recording state
transitions with the `record_history` flag; this is useful while developing finite state machines.

Every transition in your state machine is represented by a method inside the class you annotated 
with `@fineas.state_machihe()`.  To turn a method into a transition, decorate it with 
`@fineas.transition()` and supply one or more source states for the transition, and exactly one
destination state.  You can also define a state to transition to if an exception is raised inside 
your method (there is also a flag to enable or disable re-raising that exception).  If your method
accepts a parameter named `fail_transition`, its value will be a callable your method can invoke to
cause the transition to fail while still allowing your method to return a value to its caller.  You
may also pass a `fail_state` parameter to the decorator, and when `fail_transition` is invoked, your
instance will be transitioned to the given state.

When any method annotated with `@fineas.transistion()` is called, the following steps happen:

1) Acquire a lock over the receiving instance.
1) Fineas validates that the receiving instance's state is in the sources passed to 
   `@fineas.transition()`
   - If it is not, a TransitionException is raised.
1) The decorated method is invoked, passing `fail_transistion` if able.
1) If the decorated method raises an exception:
   - If `error_state` was passed, immediately transition to that state.
   - If `reraise_error` is True, re-raise the exception.
   - Return.
1) If `fail_transition` was called:
   - If 'fail_state' was passed, immediately transition to that state.
1) If no exception was raised and `fail_transition` was not called, transition to the destination
   state and return the value returned by the decorated method.
   
## Requirements

Python 3.6 or higher

wrapt 1.12.x

## Release Notes
1.0.0 (12 March, 2021):
- Minor Cleanup
- Move to poetry
- Basic test coverage
- Bump to 1.0.0 due to no issues being found in the last year.

0.1.0 (07 March, 2021):
- Initial Release
