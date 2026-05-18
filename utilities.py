import yaml

DEFAULT_PROMPT_PATH = "./prompts/system_prompt_main.yaml"


def load_prompt(path: str = DEFAULT_PROMPT_PATH, subs: dict | None = None) -> str | None:
    """Load a prompt YAML from a file path and optionally substitute placeholders."""
    try:
        with open(path, "r", encoding="utf-8") as file:
            prompt = yaml.safe_load(file)
            if subs:
                return prompt["prompt"].format_map(subs)
            return prompt["prompt"]
    except yaml.YAMLError as error:
        print(f"Failed to parse YAML at {path}: {error}")
        return None
    except FileNotFoundError:
        print(f"Prompt file not found: {path}")
        return None


def parse_prompt(content: str, subs: dict | None = None) -> str | None:
    """Parse a prompt YAML from a raw string (e.g. uploaded by the browser) and substitute."""
    try:
        data = yaml.safe_load(content)
        raw = data["prompt"]
        if subs:
            return raw.format_map(subs)
        return raw
    except yaml.YAMLError as error:
        print(f"Failed to parse prompt content: {error}")
        return None
    except (KeyError, TypeError) as error:
        print(f"Prompt YAML missing 'prompt' key: {error}")
        return None
