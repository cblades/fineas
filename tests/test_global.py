import pytest

from fineas import state_machine, TransitionException


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
        error_state='cancelled',
        failed_state='retry')
    def run(self, fail_transition):
        # do work
        status = self._do_work()

        if not status:
            fail_transition()

    @state_machine.transition(
        source='retry',
        dest='run',
        error_state='cancelled',
        failed_state='too_many_failures'
    )
    def try_again(self, times, fail_transition):
        raise RuntimeError(f'failed after trying {times} times.')

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


def test_initial_state():
    t = TestMachine()
    assert t.state == 'new'


def test_simple_transition():
    t = TestMachine()
    t.got_config({})
    assert t.state == 'configured'


def test_failed_transition():
    t = TestMachine()
    t.got_config({})
    t.ready()
    t.run()
    assert t.state == 'retry'


def test_error_transition():
    t = TestMachine()
    t.got_config({})
    t.ready()
    t.run()
    with pytest.raises(RuntimeError):
        t.try_again(2)
    assert t.state == 'cancelled'


def test_invalid_transition():
    t = TestMachine()
    with pytest.raises(TransitionException) as exc:
        t.ready()

    assert str(exc.value) == 'Wrong state for transition. Expected ((configured)--[ready]->(' \
                             'scheduled)), but was (new)--[ready]->(scheduled).'
