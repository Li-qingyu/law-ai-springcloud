from dataclasses import dataclass, field


@dataclass
class AiConfig:
    provider: str = ""
    model_name: str = ""
    api_key: str = ""
    api_base_url: str = ""
    max_tokens: int = 0
    temperature: float = 0.0

    @classmethod
    def from_json(cls, data: dict) -> "AiConfig":
        return cls(
            provider=data.get("provider", ""),
            model_name=data.get("modelName", ""),
            api_key=data.get("apiKey", ""),
            api_base_url=data.get("apiBaseUrl", ""),
            max_tokens=int(data.get("maxTokens", 0)),
            temperature=float(data.get("temperature", 0)),
        )
