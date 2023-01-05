import yaml


def edit_deployment_file(file_path: str, window_time: int = 6):
    window_time = str(window_time) + "s"
    with open(file_path, 'r') as f:
        try:
            data = yaml.full_load(f)
            data["spec"]["template"]["metadata"]["annotations"]["autoscaling.knative.dev/window"] = str(window_time)
        except yaml.YAMLError as exc:
            print(exc)
    with open(file_path, 'w') as f:
        try:
            yaml.dump(data, f)
        except yaml.YAMLError as exc:
            print(exc)
    return


edit_deployment_file("deploy.yaml", 50)
