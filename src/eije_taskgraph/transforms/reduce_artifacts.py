from taskgraph.transforms.base import TransformSequence
from taskgraph.util.schema import Schema

transforms = TransformSequence()

@transforms.add
def add_noun(config, tasks):
    for task in tasks:
        for name, artifact in task['task']['payload']['artifacts'].items():
            artifact['expires'] = {'relative-datestamp': '14 days'}
        task['task']['expires'] = {'relative-datestamp': '14 days'}

        yield task
