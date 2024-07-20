from taskgraph.transforms.base import TransformSequence
from taskgraph.util.schema import Schema

transforms = TransformSequence()

@transforms.add
def add_noun(config, tasks):
    for task in tasks:
        for name, artifact in task['task']['payload']['artifacts'].items():
            if "logs/" not in name:
                artifact['expires'] = {'relative-datestamp': '1 day'}
        yield task
