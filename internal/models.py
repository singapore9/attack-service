import logging
from typing import Type, TypeVar

from pydantic import BaseModel, Extra, Field, validator

from .logger import log_step

logger = logging.getLogger(__name__)


Model = TypeVar("Model", bound="BaseModel")


class StrictBaseModel(BaseModel):
    class Config:
        extra = Extra.forbid
        allow_population_by_field_name = True

    def to_db(self):
        data = self.dict()
        data["_id"] = data["id"]
        del data["id"]
        return data

    @classmethod
    def parse_obj_from_db(cls, data: dict):
        data["id"] = data["_id"]
        del data["_id"]
        return cls.parse_obj(data)


class VMInfo(StrictBaseModel):
    id: str = Field(alias="vm_id")
    name: str
    tags: list[str]


class FirewallRule(StrictBaseModel):
    id: str = Field(alias="fw_id")
    source_tag: str
    dest_tag: str


class TagInfo(BaseModel):
    tag: str
    tagged_vm_ids: list[str]
    tags_with_access: list[str]

    class Config:
        allow_population_by_field_name = True


class CloudEnvironment(StrictBaseModel):
    machines: list[VMInfo] = Field(alias="vms")
    rules: list[FirewallRule] = Field(alias="fw_rules")

    @validator("machines")
    @log_step(logger, "validate machine IDs")
    def unique_machine_ids(cls, machines):
        vm_ids = [vm.id for vm in machines]
        assert len(vm_ids) == len(
            set(vm_ids)
        ), "VM IDs should be unique for one environment"
        return machines

    @validator("rules")
    @log_step(logger, "validate firewall rule IDs")
    def unique_rule_ids(cls, rules):
        fw_rule_ids = [fw_rule.id for fw_rule in rules]
        assert len(fw_rule_ids) == len(
            set(fw_rule_ids)
        ), "Firewall Rule IDs should be unique for one environment"
        return rules

    @classmethod
    @log_step(logger, "parse cloud schema")
    def parse_raw(cls: Type["Model"], *args, **kwargs) -> "Model":
        return super().parse_raw(*args, **kwargs)


class StatusModel(BaseModel):
    ok: bool = True
    error_msg: str = ""


class ResponseInfoModel(BaseModel):
    id: str = Field(alias="_id")
    duration: float
    path: str
    params: str = ""

    class Config:
        allow_population_by_field_name = True
