from models import Incident, IncidentRiskUpdateBody


class IncidentRepository:
    def update_risk(self, client_id: str, incident_id: str, body: IncidentRiskUpdateBody) -> Incident | None:
        raise NotImplementedError  # pragma: no cover
