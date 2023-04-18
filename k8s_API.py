from kubernetes import client, config
import subprocess
from datetime import datetime
config.load_kube_config()
ApiV1 = client.CoreV1Api()
AppV1 = client.AppsV1Api()


class KubernetesPod:
    def __init__(self, pod_name, pod_status, pod_ip, node_name, sum_pod_container, number_container_ready):
        self.pod_name = pod_name
        self.pod_status = pod_status
        self.pod_ip = pod_ip
        self.node_name = node_name
        self.sum_pod_container = sum_pod_container
        self.number_container_ready = number_container_ready

# NOTE: Event of pod


class PodEvents:
    def __init__(self, pod_name, event_time, event, event_message) -> None:
        self.pod_name = pod_name
        self.event_time = event_time
        self.event = event
        self.event_message = event_message


def list_namespaced_pod_status(target_namespace: str = "default"):
    list_pod_status = []
    api_get_pods_response = ApiV1.list_namespaced_pod(target_namespace)
    print(api_get_pods_response)
    for pod in api_get_pods_response.items:
        current_pod_name = pod.metadata.name
        current_node_name = pod.spec.node_name
        current_pod_ip = pod.status.pod_ip
        current_pod_state = ""
        if pod.metadata.deletion_timestamp != None and (pod.status.phase == 'Running' or pod.status.phase == 'Pending'):
            current_pod_state = 'Terminating'
        elif pod.status.phase == 'Pending':
            for container in pod.status.container_statuses:
                if container.state.waiting != None:
                    current_pod_state = container.state.waiting.reason
        else:
            current_pod_state = str(pod.status.phase)
        sum_pod_container = len(pod.status.container_statuses)
        number_container_ready = 0
        for container in pod.status.container_statuses:
            if container.ready == True:
                number_container_ready += 1
        list_pod_status.append(KubernetesPod(
            current_pod_name, current_pod_state, current_pod_ip, current_node_name, sum_pod_container, number_container_ready))
    return list_pod_status


def get_number_namespaced_pod_through_status(target_status: str, target_namespace: str = "default"):
    count = 0
    list_pod = list_namespaced_pod_status(target_namespace)
    for pod in list_pod:
        if pod.pod_status == target_status:
            count += 1
    return count


# NOTE: get event of pod over  pod's name
#      return array of PodEvents class

def list_namespaced_event(target_pod_name: str, target_namespace: str = "default"):
    list_pod_event = []
    events_response = ApiV1.list_namespaced_event(
        target_namespace, field_selector=f'involvedObject.name={target_pod_name}')
    for event in events_response.items:
        current_event_time = event.first_timestamp
        current_event = event.reason
        current_event_message = event.message
        if current_event_time != None:
            current_event_time = current_event_time.timestamp()
        list_pod_event.append(PodEvents(target_pod_name, current_event_time,
                                        current_event, current_event_message))
    return list_pod_event

# NOTE:- check if the image image in the pod pulled since pod started
#      - check if the image image in the pod pulled since a timestamp (optional)
#      - return True or False
def check_pod_image_pulled(target_pod: str, start_timeline: datetime = None):
    is_pulled = False
    events = list_namespaced_event(target_pod)
    for event in events:
        if start_timeline != None and event.event_time != None:
            if event.event_time < start_timeline.timestamp():
                continue
        if event.event == "Pulled":
            is_pulled = True
            break
    return is_pulled

#NOTE: return an array of object endpoint
#      only working with serverless testcase
#      not true with other testcase 
def list_namespaced_endpoints(target_namespce: str = "default"):
    list_endpoints = []
    get_endpoint_response = ApiV1.list_namespaced_endpoints(target_namespce)
    for endpoint in get_endpoint_response.items:
        entry = {
            "endpoint_name": endpoint.metadata.name,
            "endpoints": []
        }
        list_subnet = []
        if endpoint.subsets != None:
            for subnet in endpoint.subsets:
                ips = []
                ports = []
                if subnet.addresses != None:
                    for address in subnet.addresses:
                        ips.append(address.ip)
                if subnet.ports != None:
                    for port in subnet.ports:
                        ports.append(port.port)
                address = {
                    "ip": ips,
                    "port": ports
                }
                list_subnet.append(address)
        entry["endpoints"] = list_subnet
        list_endpoints.append(entry)
    return list_endpoints


def create_namespaced_service(target_service: str, target_ID: str,
                              target_service_port: int, target_namespace: str = "default"):
    service_name = target_service + "-" + target_ID + "-service"
    service_selector = target_service + "-" + target_ID + "-deployment"
    body = client.V1Service(
        api_version="v1",
        kind="Service",
        metadata=client.V1ObjectMeta(name=service_name),
        spec=client.V1ServiceSpec(
            selector={"app": service_selector, "ID": target_ID},
            type="ClusterIP",
            ports=[client.V1ServicePort(
                port=target_service_port,
                target_port="container-port")]))
    try:
        response = ApiV1.create_namespaced_service(
            namespace=target_namespace, body=body)
    except:
        return ("There is unknown error when deploy {}.".format(service_name))
    return ("Deploy {} succesfully.".format(service_name))


def create_namespaced_deployment(target_deployment: str, target_ID: str, target_image: str,
                                 target_container_port: int, target_env, target_namespace: str = "default"):
    deployment_name = target_deployment + "-" + target_ID + "-deployment"
    body = (
        client.V1Deployment(
            api_version="apps/v1",
            kind="Deployment",
            metadata=client.V1ObjectMeta(
                name=deployment_name
            ),
            spec=client.V1DeploymentSpec(
                selector=client.V1LabelSelector(
                    match_labels={"app": deployment_name, "ID": target_ID}
                ),
                template=client.V1PodTemplateSpec(
                    metadata=client.V1ObjectMeta(
                        labels={"app": deployment_name, "ID": target_ID}
                    ),
                    spec=client.V1PodSpec(
                        containers=[client.V1Container(
                            name=target_deployment,
                            image=target_image,
                            ports=[client.V1ContainerPort(
                                container_port=target_container_port,
                                name="container-port"
                            )],
                            env=target_env
                        )]
                    )
                )
            )

        )
    )
    try:
        response = AppV1.create_namespaced_deployment(
            body=body, namespace=target_namespace)
    except:
        return ("There is unknown error when deploy {}.".format(deployment_name))
    return ("Deploy {} succesfully.".format(deployment_name))


def delete_namespaced_deployment(target_deployment: str, target_ID: str, target_namespace: str = "default"):
    deployment_name = target_deployment + "-" + target_ID + "-deployment"
    try:
        AppV1.delete_namespaced_deployment(deployment_name, target_namespace)
    except:
        return ("There is unknown error when delete {}.".format(deployment_name))
    return ("Delete {} succesfully.".format(deployment_name))


def delete_namespaced_service(target_service: str, target_ID: str, target_namespace: str = "default"):
    service_name = target_service + "-" + target_ID + "-service"
    try:
        ApiV1.delete_namespaced_service(service_name, target_namespace)
    except:
        return ("There is unknown error when delete {}.".format(service_name))
    return ("Delete {} succesfully.".format(service_name))


def connect_get_namespaced_pod_exec(target_command: str, target_name: str):
    command = "kubectl exec -it {} -- {} ".format(target_name, target_command)
    output = subprocess.check_output(['/bin/bash', '-c', command])
    print(output)

a = list_namespaced_endpoints()
print(a)
for i in a:
    print(i['endpoint_name'])
    for j in i['endpoints']:
        print(j['ip'])
        print(j['port'])

# a = check_pod_image_pulled(
#     "source-streaming-deployment-7c57ffbd6b-s45nm")
# print(a)
# a = list_namespaced_event("source-streaming-deployment-7c57ffbd6b-xxzm4")
# i: PodEvents
# for i in a:
#     print(i.pod_name)
#     print(i.event_time)
#     print(i.event_message)
#     print(i.event)


# a = list_namespaced_pod_status()
# i:KubernetesPod
# for i in a:
#     print(i.pod_name)
#     print(i.pod_status)
#     print(i.pod_ip)
#     print("{}/{}".format(i.number_container_ready,i.sum_pod_container))
