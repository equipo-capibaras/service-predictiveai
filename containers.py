from dependency_injector import providers
from dependency_injector.containers import DeclarativeContainer, WiringConfiguration

from repositories.rest import RestIncidentRepository, RestUserRepository


class Container(DeclarativeContainer):
    wiring_config = WiringConfiguration(packages=['blueprints'])
    config = providers.Configuration()

    incident_repo = providers.ThreadSafeSingleton(
        RestIncidentRepository, base_url=config.svc.incident.url, token_provider=config.svc.incident.token_provider
    )

    user_repo = providers.ThreadSafeSingleton(
        RestUserRepository,
        base_url=config.svc.user.url,
        token_provider=config.svc.user.token_provider,
    )
