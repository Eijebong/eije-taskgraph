from taskgraph.transforms.run import run_task_using
from taskgraph.transforms.task import payload_builder, taskref_or_string
from voluptuous import Required

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
