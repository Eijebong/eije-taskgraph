from taskgraph.transforms.run import run_task_using
from taskgraph.transforms.task import payload_builder, taskref_or_string
from taskgraph.morph import register_morph
from voluptuous import Required
from taskgraph.graph import Graph
from taskgraph.taskgraph import TaskGraph

def register(graph_config):
    graph_config['workers']['aliases'] = {
        "linux-small": {
            "provisioner": "ap",
            "implementation": "docker-worker",
            "os": "linux",
            "worker-type": "linux-small",
        },
        "linux-medium": {
            "provisioner": "ap",
            "implementation": "docker-worker",
            "os": "linux",
            "worker-type": "linux-medium",
        },
        "images": {
            "provisioner": "ap",
            "implementation": "docker-worker",
            "os": "linux",
            "worker-type": "linux-medium",
        },
        "argocd-webhook": {
            "provisioner": "scriptworker",
            "implementation": "argocd-webhook",
            "os": "scriptworker",
            "worker-type": "argocd-webhook",
        },
        "githubscript": {
            "provisioner": "scriptworker",
            "implementation": "githubscript",
            "os": "scriptworker",
            "worker-type": "githubscript",
        },
        "apdiffscript": {
            "provisioner": "scriptworker",
            "implementation": "apdiffscript",
            "os": "scriptworker",
            "worker-type": "apdiffscript",
        },
    }

@run_task_using("argocd-webhook", "argocd-webhook")
def run_webhook(config, task, taskdesc):
    pass

@payload_builder("argocd-webhook", schema={})
def build_argocd_payload(config, task, task_def):
    pass

@payload_builder("githubscript-apdiff", schema={
    Required("diff-task"): taskref_or_string,
})
def build_githubscript_apdiff(config, task, task_def):
    task_def["payload"] = {
        "diff-task": task["worker"]["diff-task"]
    }

@payload_builder("githubscript-aptest", schema={
    Required("test-task"): taskref_or_string,
})
def build_githubscript_aptest(config, task, task_def):
    task_def["payload"] = {
        "test-task": task["worker"]["test-task"]
    }

@payload_builder("apdiffscript-diff", schema={
    Required("diff-task"): taskref_or_string,
})
def build_apdiffscript_diff(config, task, task_def):
    task_def["payload"] = {
        "diff-task": task["worker"]["diff-task"]
    }


@register_morph
def handle_very_soft_if_deps(taskgraph, label_to_task_id, parameters, graph_config):
    new_edges = set(taskgraph.graph.edges)
    new_tasks = taskgraph.tasks.copy()

    for task in taskgraph:
        very_soft_if_deps = task.attributes.get("very-soft-if-deps")
        if not very_soft_if_deps:
            continue


        if not any(very_soft_if_dep in label_to_task_id for very_soft_if_dep in very_soft_if_deps):
            print(f"Removing {task.label} because all its deps are gone")
            del new_tasks[label_to_task_id[task.label]]
            continue

        for very_soft_if_dep in very_soft_if_deps:
            if very_soft_if_dep in label_to_task_id:
                new_edges.add((task.task_id, label_to_task_id[very_soft_if_dep], very_soft_if_dep))
                task.dependencies[very_soft_if_dep] = label_to_task_id[very_soft_if_dep]

    new_taskgraph = TaskGraph(new_tasks, Graph(set(new_tasks), new_edges))
    return new_taskgraph, label_to_task_id
