from typing import Any, cast

from faker import Faker
from unittest_parametrize import ParametrizedTestCase

from app import create_app
from models import Action, Channel, Plan, Role


class TestEvent(ParametrizedTestCase):
    def setUp(self) -> None:
        self.faker = Faker()

        self.app = create_app()
        self.client = self.app.test_client()

    def gen_random_event_data(self, channel: Channel | None = None) -> dict[str, Any]:
        return {
            'id': cast(str, self.faker.uuid4()),
            'name': self.faker.sentence(3),
            'channel': channel or self.faker.random_element(list(Channel)),
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
                    'action': Action.CREATED,
                    'description': self.faker.text(200),
                },
            ],
            'client': {
                'id': cast(str, self.faker.uuid4()),
                'name': self.faker.name(),
                'emailIncidents': self.faker.email(),
                'plan': self.faker.random_element(list(Plan)),
            },
        }

    def test_update(self) -> None:
        data = self.gen_random_event_data()

        with self.assertLogs():
            resp = self.client.post('/api/v1/incident-update/predictiveai', json=data)

        self.assertEqual(resp.status_code, 200)
