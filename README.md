# kwatch
simple Kubernetes monitoring tools


### Workshoping k cmds

 kubectl get pods -o custom-columns="POD:metadata.name,STATE:status.containerStatuses[*].state.waiting.reason" -A

 kubectl get pods -o custom-columns="POD:metadata.name,STATE:status.reason" -A

 kubectl get pods -o custom-columns="POD:metadata.name,PHASE:status.phase"