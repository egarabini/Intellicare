"""Camada de persistencia do modulo de comunicacao."""

from comunicacao.storage.repository import (
    InMemoryPatientRoomRepository,
    PatientRoomRepository,
    PostgresPatientRoomRepository,
    build_patient_room_repository,
)
from comunicacao.storage.rules_repository import PostgresRoutingRuleStore, build_routing_rule_store
from comunicacao.storage.routing_repository import PostgresRoutingStore, build_routing_store
from comunicacao.storage.template_repository import PostgresTemplateStore, build_template_store

__all__ = [
    "PatientRoomRepository",
    "InMemoryPatientRoomRepository",
    "PostgresPatientRoomRepository",
    "build_patient_room_repository",
    "PostgresRoutingRuleStore",
    "PostgresRoutingStore",
    "PostgresTemplateStore",
    "build_routing_rule_store",
    "build_routing_store",
    "build_template_store",
]
