from dataclasses import asdict
from typing import Any, cast

import dacite
import requests

from models import Channel, Incident, IncidentRiskUpdateBody, Risk
from repositories import IncidentRepository

from .base import RestBaseRepository
from .util import TokenProvider


class RestIncidentRepository(IncidentRepository, RestBaseRepository):
    def __init__(self, base_url: str, token_provider: TokenProvider | None) -> None:
        RestBaseRepository.__init__(self, base_url, token_provider)

    def update_risk(self, client_id: str, incident_id: str, body: IncidentRiskUpdateBody) -> Incident | None:
        dict_body = asdict(body)
        resp = self.authenticated_put(
            url=f'{self.base_url}/api/v1/clients/{client_id}/incidents/{incident_id}/update-risk',
            body=dict_body,
        )

        if resp.status_code == requests.codes.ok:
            data = cast(dict[str, Any], resp.json())
            data['incident_id'] = incident_id
            data['client_id'] = client_id

            type_hooks = {Channel: lambda s: Channel(s.lower()), Risk: lambda s: Risk(s)}
            return dacite.from_dict(data_class=Incident, data=data, config=dacite.Config(type_hooks=type_hooks))

        if resp.status_code == requests.codes.not_found:
            return None

        self.unexpected_error(resp)  # noqa: RET503
