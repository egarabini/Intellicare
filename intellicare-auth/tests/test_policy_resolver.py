import pytest
import json
from unittest.mock import AsyncMock, MagicMock
from intellicare_auth.policy_resolver import PolicyResolver

@pytest.fixture
def mock_redis():
    redis = AsyncMock()
    return redis

@pytest.fixture
def mock_session():
    session = AsyncMock()
    return session

@pytest.fixture
def resolver(mock_session, mock_redis):
    return PolicyResolver(session=mock_session, redis=mock_redis)

@pytest.mark.asyncio
async def test_policy_resolver_redis_cache_hit(resolver, mock_redis, mock_session):
    # Setup cache
    mock_redis.get.return_value = json.dumps({"is_admin": True, "resource_rules": []})
    
    policy = await resolver.resolve("tenant1", "user1")
    
    assert policy == {"is_admin": True, "resource_rules": []}
    mock_redis.get.assert_called_once_with("policy:tenant1:user1")
    # Verify DB wasn't queried
    mock_session.execute.assert_not_called()

@pytest.mark.asyncio
async def test_policy_resolver_db_hit_is_admin(resolver, mock_redis, mock_session):
    # Miss cache
    mock_redis.get.return_value = None
    
    # DB Hit
    mock_result = MagicMock()
    # (is_admin, parameters, resource_rules)
    mock_result.fetchone.return_value = (True, None, None)
    mock_session.execute.return_value = mock_result
    
    policy = await resolver.resolve("tenant1", "user1")
    
    assert policy == {"is_admin": True, "resource_rules": []}
    mock_redis.set.assert_called_once()
    assert "policy:tenant1:user1" in mock_redis.set.call_args[0]

@pytest.mark.asyncio
async def test_policy_resolver_db_hit_with_parameters(resolver, mock_redis, mock_session):
    # Miss cache
    mock_redis.get.return_value = None
    
    # DB Hit: Not admin, has param %profile -> Practitioner/123
    rules = [{"resource_type": "Observation", "criteria": "Observation?performer=%profile"}]
    parameters = {"profile": "Practitioner/123"}
    
    mock_result = MagicMock()
    mock_result.fetchone.return_value = (False, parameters, rules)
    mock_session.execute.return_value = mock_result
    
    policy = await resolver.resolve("tenant1", "user1")
    
    assert policy["is_admin"] is False
    assert len(policy["resource_rules"]) == 1
    # Check if parameter was successfully substituted
    assert policy["resource_rules"][0]["criteria"] == "Observation?performer=Practitioner/123"

@pytest.mark.asyncio
async def test_policy_resolver_no_membership(resolver, mock_redis, mock_session):
    # Miss cache
    mock_redis.get.return_value = None
    
    # DB Miss
    mock_result = MagicMock()
    mock_result.fetchone.return_value = None
    mock_session.execute.return_value = mock_result
    
    policy = await resolver.resolve("tenant1", "user1")
    
    # Deny All policy
    assert policy == {}
