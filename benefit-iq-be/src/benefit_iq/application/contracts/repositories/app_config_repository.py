"""AppConfig Repository Interface Contract."""

from abc import ABC, abstractmethod

from benefit_iq.domain.entities.app_config import AppConfig


class AppConfigRepository(ABC):
    """Abstract contract for dynamic application configuration persistence."""

    @abstractmethod
    async def create(self, config: AppConfig) -> AppConfig:
        """Creates a new application configuration record."""
        ...

    @abstractmethod
    async def get_by_key(
        self, application: str, environment: str, config_key: str
    ) -> AppConfig | None:
        """Retrieves a configuration record by application, environment, and key."""
        ...

    @abstractmethod
    async def list_configs(self, application: str, environment: str) -> list[AppConfig]:
        """Lists active configuration entries for a specific application and environment."""
        ...

    @abstractmethod
    async def update(self, config: AppConfig) -> AppConfig:
        """Updates an existing configuration record."""
        ...

    @abstractmethod
    async def delete(self, application: str, environment: str, config_key: str) -> bool:
        """Soft deletes / deactivates a configuration record."""
        ...
