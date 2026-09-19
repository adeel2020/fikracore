"""Base contract model for Zaki v1 domain objects."""

from __future__ import annotations

import pydantic
from typing import Any
from pydantic import BaseModel

IS_PYDANTIC_V2 = getattr(pydantic, "__version__", "1.").startswith("2")

if IS_PYDANTIC_V2:
    from pydantic import ConfigDict

    class BaseContract(BaseModel):
        model_config = ConfigDict(extra="ignore", populate_by_name=True)
else:
    class BaseContract(BaseModel):
        class Config:
            extra = "ignore"
            allow_population_by_field_name = True

        @classmethod
        def model_validate(cls, obj: Any):
            if isinstance(obj, cls):
                return obj
            return cls.parse_obj(obj)

        def model_dump(self, mode: str = "python", **kwargs) -> dict:
            import json
            if mode == "json":
                return json.loads(self.json(**kwargs))
            return self.dict(**kwargs)
