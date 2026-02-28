"""Staging Strategy Factory — cria estrategias de estadiamento."""

import logging
from typing import Type

from oswaldo.engine.staging.base import GenericRangeStagingStrategy, StagingStrategy
from oswaldo.engine.staging.ckd_staging import KDIGOStagingStrategy
from oswaldo.engine.staging.dm2_staging import ADAStagingStrategy
from oswaldo.engine.staging.has_staging import ESCESHStagingStrategy
from oswaldo.profiles.models import DiseaseProfile

logger = logging.getLogger(__name__)


class StagingStrategyFactory:
    """Factory para criar estrategias de estadiamento."""

    _strategies: dict[str, Type[StagingStrategy]] = {
        "generic_range": GenericRangeStagingStrategy,
        "kdigo": KDIGOStagingStrategy,
        "ada": ADAStagingStrategy,
        "escesh": ESCESHStagingStrategy,
    }

    @classmethod
    def register_strategy(cls, strategy_name: str, strategy_class: Type[StagingStrategy]) -> None:
        cls._strategies[strategy_name] = strategy_class

    @classmethod
    def create(cls, profile: DiseaseProfile) -> StagingStrategy:
        strategy_name = profile.staging.strategy
        if strategy_name not in cls._strategies:
            logger.warning("Estrategia '%s' nao encontrada, usando GenericRange", strategy_name)
            strategy_name = "generic_range"
        return cls._strategies[strategy_name](profile)

    @classmethod
    def list_strategies(cls) -> list[str]:
        return list(cls._strategies.keys())
