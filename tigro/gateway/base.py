from abc import ABC, abstractmethod

class BaseGateway(ABC):
    @abstractmethod
    async def run(self):
        ... 