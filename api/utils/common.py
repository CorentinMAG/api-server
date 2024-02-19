from copy import deepcopy

def parse_params(params: dict[str, str]) -> dict[str, str | int | bool]:
    new_params = deepcopy(params)
    for key, value in new_params.items():
        if value.lower() in ("true", "false"):
            new_params[key] = True if value.lower() == "true" else False
        elif value.isdigit():
            new_params[key] = int(value)
    return new_params