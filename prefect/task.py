import copy
import datetime
import prefect
import prefect.triggers


class Task:
    """
    Tasks are basic units of work. Each task performs a specific funtion.
    """

    def __init__(
            self,
            name=None,
            flow=None,
            fn=None,
            params=None,
            retries=0,
            retry_delay=datetime.timedelta(minutes=5),
            trigger=None):
        """
        fn: By default, the Task's run() method calls this function.
        retries: the number of times this task can be retried. -1 indicates
            an infinite number of times.
        """

        self.fn = fn

        if flow is None:
            flow = prefect.flow._CONTEXT_MANAGER_FLOW
            if flow is None:
                raise ValueError(
                    'Tasks must be created with a Flow or inside '
                    'a Flow context manager.')
        self.flow = flow

        if name is None:
            name = self.fn.__name__

        if not isinstance(name, str):
            raise TypeError(
                'Name must be a string; received {}'.format(type(name)))
        self.name = name

        if not isinstance(retries, int):
            raise TypeError(
                'Retries must be an int; received {}'.format(retries))
        self.retries = retries

        if not isinstance(retry_delay, datetime.timedelta):
            raise TypeError(
                'Retry delay must be a timedelta; received {}'.format(
                    type(retry_delay)))
        self.retry_delay = retry_delay

        if trigger is None:
            trigger = prefect.triggers.all_success
        self.trigger = trigger

        #TODO params come from Flow
        self.params = params

        self.flow.add_task(self)

    @property
    def id(self):
        return '{}/{}'.format(self.flow.id, self.name)

    def run_before(self, *tasks):
        """
        Adds a relationship to the Flow so that this task runs before another
        task.
        """
        for t in tasks:
            self.flow.add_task_relationship(before=self, after=t)

    def run_after(self, *tasks):
        """
        Adds a relationship to the Flow so that this task runs after another
        task.
        """
        for t in tasks:
            self.flow.add_task_relationship(before=t, after=self)

    def run(self, *args, **kwargs):
        if self.fn is not None:
            return self.fn(*args, **kwargs)

    # Serialization  ------------------------------------------------

    def serialize(self):
        return prefect.utilities.serialize.serialize(self)

    @staticmethod
    def from_serialized(serialized_obj):
        deserialized = prefect.utilities.serialize.deserialize(serialized_obj)
        if not isinstance(deserialized, Task):
            raise TypeError('Deserialized object is not a Task!')
        return deserialized

    # Sugar ---------------------------------------------------------

    def __or__(self, task):
        """ self | task -> self.run_before(task)"""
        self.run_before(task)

    def __rshift__(self, task):
        """ self >> task -> self.run_before(task)"""
        self.run_before(task)

    def __lshift__(self, task):
        """ self << task -> self.run_after(task)"""
        self.run_after(task)

    # Serialization  ------------------------------------------------

    def serialize(self):
        return prefect.utilities.serialize.serialize(self)

    @staticmethod
    def from_serialized(serialized_obj):
        deserialized = prefect.utilities.serialize.deserialize(serialized_obj)
        if not isinstance(deserialized, Task):
            raise TypeError('Deserialized object is not a Task!')
        return deserialized

    # ORM ----------------------------------------------------------

    def as_orm(self):
        return prefect.models.TaskModel(
            _id=self.id,
            name=self.name,
            flow=self.flow.as_orm())

    def save(self):
        model = self.as_orm()
        model.save()
        return model

    def reload(self):
        model = self.as_orm()
        model.reload()
        self.name = model.name
