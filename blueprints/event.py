from dataclasses import dataclass, field
from datetime import datetime
from random import choice
from typing import cast

import marshmallow_dataclass
from dependency_injector.wiring import Provide
from flask import Blueprint, Response, current_app, request
from flask.views import MethodView

from containers import Container
from models import Action, Channel, HistoryEntry, Incident, IncidentRiskUpdateBody, Plan, Risk, Role
from repositories import IncidentRepository

from .util import class_route, json_response

blp = Blueprint('Event', __name__)
MAX_ESCALATIONS = 3


@dataclass
class UserBody:
    id: str
    name: str
    email: str
    role: Role = field(metadata={'by_value': True})


@dataclass
class ClientBody:
    id: str
    name: str
    email_incidents: str
    plan: Plan = field(metadata={'by_value': True})


@dataclass
class HistoryBody:
    seq: int
    date: datetime
    action: Action = field(metadata={'by_value': True})
    description: str


@dataclass
class EventBody:
    id: str
    name: str
    channel: Channel = field(metadata={'by_value': True})
    language: str
    reported_by: UserBody
    created_by: UserBody
    assigned_to: UserBody
    history: list[HistoryBody]
    client: ClientBody
    risk: Risk | None = field(default=None, metadata={'by_value': True})


def load_event_data() -> EventBody:
    req_json = request.get_json(silent=True)
    if req_json is None:
        raise ValueError('Invalid JSON body')

    req_json['reported_by'] = req_json.pop('reportedBy')
    req_json['created_by'] = req_json.pop('createdBy')
    req_json['assigned_to'] = req_json.pop('assignedTo')
    req_json['client']['email_incidents'] = req_json['client'].pop('emailIncidents')

    event_schema = marshmallow_dataclass.class_schema(EventBody)()
    return cast(EventBody, event_schema.load(req_json))


@class_route(blp, '/api/v1/incident-update/predictiveai')
class UpdateEvent(MethodView):
    init_every_request = False

    response = json_response({'message': 'Event processed.', 'code': 200}, 200)

    def log_update_result(self, incident_id: str, incident: Incident | None) -> None:
        if incident is None:
            current_app.logger.info('Incident %s risk could not be updated', incident_id)
        else:
            current_app.logger.info('Incident %s risk updated', incident_id)

    def set_risk(self, history: HistoryEntry | None) -> Risk:
        escalations = sum(1 for entry in history if entry.action == Action.ESCALATED)

        if escalations >= MAX_ESCALATIONS:
            return Risk.HIGH

        return choice(list(Risk))  # noqa: S311

    def post(self, incident_repo: IncidentRepository = Provide[Container.incident_repo]) -> Response:
        data = load_event_data()

        if data.history[-1].action != Action.CLOSED:
            new_risk = self.set_risk(history=data.history)
            body = IncidentRiskUpdateBody(risk=new_risk)

            incident = None
            incident = incident_repo.update_risk(client_id=data.client.id, incident_id=data.id, body=body)
            self.log_update_result(data.id, incident)

        return self.response
