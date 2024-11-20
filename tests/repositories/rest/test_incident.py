from typing import Any, cast
from unittest.mock import Mock

import responses
from faker import Faker
from requests import HTTPError
from unittest_parametrize import ParametrizedTestCase, parametrize

from models import Incident, IncidentRiskUpdateBody, Risk
from repositories.rest import RestIncidentRepository, TokenProvider


class TestRestIncidentRepository(ParametrizedTestCase):
    def setUp(self) -> None:
        self.faker = Faker()
        self.base_url = self.faker.url().rstrip('/')
        self.repo = RestIncidentRepository(self.base_url, None)

    def gen_fake_incident_response(self, client_id: str, incident_id: str, risk: Risk) -> dict[str, Any]:
        """Generate a fake response for an incident."""
        return {
            'id': incident_id,
            'client_id': client_id,
            'name': self.faker.sentence(nb_words=3),
            'channel': 'email',
            'reported_by': str(self.faker.uuid4()),
            'created_by': str(self.faker.uuid4()),
            'assigned_to': str(self.faker.uuid4()),
            'risk': risk.value,
        }

    def test_authenticated_put_without_token_provider(self) -> None:
        repo = RestIncidentRepository(self.base_url, None)

        with responses.RequestsMock() as rsps:
            rsps.put(self.base_url)
            repo.authenticated_put(self.base_url, body={})
            self.assertNotIn('Authorization', rsps.calls[0].request.headers)

    def test_authenticated_put_with_token_provider(self) -> None:
        token = self.faker.pystr()
        token_provider = Mock(TokenProvider)
        cast(Mock, token_provider.get_token).return_value = token

        repo = RestIncidentRepository(self.base_url, token_provider)

        with responses.RequestsMock() as rsps:
            rsps.put(self.base_url)
            repo.authenticated_put(self.base_url, body={})
            self.assertEqual(rsps.calls[0].request.headers['Authorization'], f'Bearer {token}')

    @parametrize(
        ('status_code', 'risk', 'expected_result'),
        [
            (200, Risk.HIGH, True),  # Success case
            (404, Risk.LOW, False),  # Not found
        ],
    )
    def test_update_risk(self, status_code: int, risk: Risk, expected_result: bool) -> None:  # noqa: FBT001
        client_id = cast(str, self.faker.uuid4())
        incident_id = cast(str, self.faker.uuid4())
        update_body = IncidentRiskUpdateBody(risk=risk)

        response_data = self.gen_fake_incident_response(client_id, incident_id, risk)

        with responses.RequestsMock() as rsps:
            rsps.put(
                f'{self.base_url}/api/v1/clients/{client_id}/incidents/{incident_id}/update-risk',
                json=response_data if status_code == 200 else {'message': 'Not found'},  # noqa: PLR2004
                status=status_code,
            )

            if expected_result:
                result = self.repo.update_risk(client_id, incident_id, update_body)
                if result is not None:
                    self.assertIsInstance(result, Incident)
                    self.assertEqual(result.risk, risk)
            else:
                result = self.repo.update_risk(client_id, incident_id, update_body)
                self.assertIsNone(result)

    @parametrize(
        ('status_code',),
        [
            (400,),
            (500,),
        ],
    )
    def test_update_risk_unexpected_error(self, status_code: int) -> None:
        client_id = cast(str, self.faker.uuid4())
        incident_id = cast(str, self.faker.uuid4())
        update_body = IncidentRiskUpdateBody(risk=Risk.MEDIUM)

        with responses.RequestsMock() as rsps, self.assertRaises(HTTPError):
            rsps.put(
                f'{self.base_url}/api/v1/clients/{client_id}/incidents/{incident_id}/update-risk',
                status=status_code,
            )

            self.repo.update_risk(client_id, incident_id, update_body)
