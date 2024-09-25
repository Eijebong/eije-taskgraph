from taskgraph.transforms.base import TransformSequence
from taskgraph.util.schema import Schema
from taskgraph.util.time import json_time_from_now

transforms = TransformSequence()

@transforms.add
def add_noun(config, tasks):
    for task in tasks:
        for name, artifact in task['task']['payload']['artifacts'].items():
            artifact['expires'] = {'relative-datestamp': '14 days'}
        task['expires'] = json_time_from_now('14 days')
        yield task
