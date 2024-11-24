from dataclasses import dataclass, field

import marshmallow.validate

from .risk import Risk


@dataclass
class IncidentRiskUpdateBody:
    risk: Risk | None = field(metadata={'validate': marshmallow.validate.OneOf([Risk.HIGH, Risk.LOW, Risk.MEDIUM])})
