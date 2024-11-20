from models import HistoryEntry, IncidentRiskUpdateBody


class IncidentRepository:
    def update_risk(self, client_id: str, incident_id: str, body: IncidentRiskUpdateBody) -> HistoryEntry | None:
        raise NotImplementedError  # pragma: no cover
