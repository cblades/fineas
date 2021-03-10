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