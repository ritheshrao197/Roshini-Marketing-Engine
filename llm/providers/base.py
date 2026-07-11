import abc

class BaseProvider(abc.ABC):
    """
    Base class interface for all AI model providers.
    All subclasses must implement the asynchronous 'generate' method.
    """
    
    @abc.abstractmethod
    async def generate(
        self,
        model_name: str,
        prompt: str,
        system_instruction: str = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        json_format: bool = False,
        timeout: int = 60
    ) -> dict:
        """
        Executes text generation using the configured model and provider.
        Returns:
            dict: {
                "text": str,
                "tokens": int,
                "latency": float,
                "cost": float,
                "status": str ("success" | "failure"),
                "error": str | None
            }
        """
        pass
