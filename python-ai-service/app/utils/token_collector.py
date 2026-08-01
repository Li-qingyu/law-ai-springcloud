from dataclasses import dataclass


def extract_usage_metadata(message) -> dict | None:
    """从 AIMessage 中提取 token 使用量"""
    if message is None:
        return None
    # LangChain AIMessage.usage_metadata
    usage = getattr(message, "usage_metadata", None)
    if usage and isinstance(usage, dict):
        return {
            "input_tokens": usage.get("input_tokens", 0),
            "output_tokens": usage.get("output_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
        }
    # response_metadata.token_usage 兜底
    metadata = getattr(message, "response_metadata", {}) or {}
    token_usage = metadata.get("token_usage", {})
    if token_usage:
        return {
            "input_tokens": token_usage.get("input_tokens", 0),
            "output_tokens": token_usage.get("output_tokens", 0),
            "total_tokens": token_usage.get("total_tokens", 0),
        }
    return None


@dataclass
class TokenCollector:
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0

    def add(self, usage_metadata: dict | None):
        if usage_metadata:
            self.input_tokens += usage_metadata.get("input_tokens", 0)
            self.output_tokens += usage_metadata.get("output_tokens", 0)
            self.total_tokens += usage_metadata.get("total_tokens", 0)

    def to_dict(self) -> dict:
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens
        }
