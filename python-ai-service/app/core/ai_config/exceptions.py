class AiConfigError(Exception):
    pass

class AiConfigNotFoundError(AiConfigError):
    pass

class AiConfigSourceError(AiConfigError):
    def __init__(self, source: str, message: str):
        self.source = source
        super().__init__(f"[{source}] {message}")
