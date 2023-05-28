from pydantic import BaseModel, Extra, Field


class StrictBaseModel(BaseModel):
    class Config:
        extra = Extra.forbid
        allow_population_by_field_name = True


class VMInfo(StrictBaseModel):
    id: str = Field(alias="vm_id")
    name: str
    tags: list[str]


class FirewallRule(StrictBaseModel):
    id: str = Field(alias="fw_id")
    source_tag: str
    dest_tag: str


class CloudEnvironment(StrictBaseModel):
    machines: list[VMInfo] = Field(alias="vms")
    rules: list[FirewallRule] = Field(alias="fw_rules")
