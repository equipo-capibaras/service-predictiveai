from typing import Any, cast
from unittest.mock import Mock, patch

from faker import Faker
from unittest_parametrize import ParametrizedTestCase, parametrize

from app import create_app
from blueprints.event import UpdateEvent
from models import Action, Channel, Incident, Plan, Risk, Role
from repositories import IncidentRepository


class TestUpdateEvent(ParametrizedTestCase):
    def setUp(self) -> None:
        self.faker = Faker()
        self.app = create_app()
        self.client = self.app.test_client()
        self.incident_repo_mock = Mock(IncidentRepository)

    def gen_random_event_data(self, *, action: Action, risk: Risk | None = None) -> dict[str, Any]:
        return {
            'id': cast(str, self.faker.uuid4()),
            'name': self.faker.sentence(3),
            'channel': self.faker.random_element(list(Channel)),
            'language': self.faker.random_element(['es', 'pt']),
            'reportedBy': {
                'id': cast(str, self.faker.uuid4()),
                'name': self.faker.name(),
                'email': self.faker.email(),
                'role': Role.USER,
            },
            'createdBy': {
                'id': cast(str, self.faker.uuid4()),
                'name': self.faker.name(),
                'email': self.faker.email(),
                'role': Role.USER,
            },
            'assignedTo': {
                'id': cast(str, self.faker.uuid4()),
                'name': self.faker.name(),
                'email': self.faker.email(),
                'role': Role.AGENT,
            },
            'history': [
                {
                    'seq': 0,
                    'date': self.faker.past_datetime().isoformat().replace('+00:00', 'Z'),
                    'action': action,
                    'description': self.faker.text(200),
                }
            ],
            'client': {
                'id': cast(str, self.faker.uuid4()),
                'name': self.faker.company(),
                'emailIncidents': self.faker.email(),
                'plan': Plan.EMPRESARIO_PLUS,
            },
            'risk': risk.value if risk else None,
        }

    @parametrize(
        ('action', 'escalations', 'expected_update_call', 'expected_status'),
        [
            (Action.CREATED, 0, True, 200),
            (Action.ESCALATED, 3, True, 200),
            (Action.CLOSED, 0, False, 200),
        ],
    )
    def test_update_risk(self, action: Action, escalations: int, expected_update_call: bool, expected_status: int) -> None:  # noqa: FBT001
        data = self.gen_random_event_data(action=action)
        for i in range(1, escalations + 1):
            data['history'].append(
                {
                    'seq': i,
                    'date': self.faker.past_datetime().isoformat().replace('+00:00', 'Z'),
                    'action': Action.ESCALATED,
                    'description': self.faker.text(200),
                }
            )

        # Asegúrate de limpiar el mock antes de la prueba
        self.incident_repo_mock.update_risk.reset_mock()

        with self.app.container.incident_repo.override(self.incident_repo_mock):
            response = self.client.post('/api/v1/incident-risk-updated/predictiveai', json=data)

        # Validar si `update_risk` fue llamado o no
        if expected_update_call:
            self.incident_repo_mock.update_risk.assert_called_once()
        else:
            self.incident_repo_mock.update_risk.assert_not_called()

        # Validar el código de estado
        self.assertEqual(response.status_code, expected_status)

        # Validar la respuesta esperada
        expected_response = {'message': 'Event processed.', 'code': 200}
        self.assertEqual(response.json, expected_response)

    @parametrize(
        ('incident', 'expected_log_message'),
        [
            (None, 'Incident %s risk could not be updated'),
            (Mock(), 'Incident %s risk updated'),
        ],
    )
    def test_log_update_result(self, incident: Incident | None, expected_log_message: str) -> None:
        incident_id = cast(str, self.faker.uuid4())
        view = UpdateEvent()

        with self.app.app_context(), patch.object(self.app.logger, 'info') as mock_logger_info:
            view.log_update_result(incident_id, incident)
            mock_logger_info.assert_called_once_with(expected_log_message, incident_id)
