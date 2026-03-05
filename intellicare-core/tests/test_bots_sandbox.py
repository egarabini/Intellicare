"""
Tests for Bot Sandbox security enforcement.
"""
import pytest
from intellicare_core.bots.sandbox import BotSandbox
from intellicare_core.bots.context import BotExecutionContext, EventMetadata, BotLogger
from intellicare_core.bots.client import IntelliCareClient

@pytest.fixture
def mock_context():
    return BotExecutionContext(
        input_resource={"resourceType": "Patient", "id": "123"},
        fhir_client=IntelliCareClient(tenant_id="tenant-1"),
        secrets={"API_KEY": "supersecret"},
        event_metadata=EventMetadata(interaction="create"),
        logger=BotLogger()
    )

def test_sandbox_allows_basic_math_and_logic(mock_context):
    """Test that a normal python function successfully executes."""
    sandbox = BotSandbox()
    code = '''
def add(a, b):
    return a + b
x = add(1, 2)
print("Result is", x)
'''
    result = sandbox.execute(code, mock_context)
    assert result["success"] is True
    assert result["error"] is None
    assert "Result is 3" in mock_context.logger.get_log_output()

def test_sandbox_blocks_filesystem_access(mock_context):
    """Test that trying to open a file fails due to restricted builtins."""
    sandbox = BotSandbox()
    code = '''
with open('/etc/passwd', 'r') as f:
    print(f.read())
'''
    result = sandbox.execute(code, mock_context)
    assert result["success"] is False
    assert "name 'open' is not defined" in result["error"]

def test_sandbox_blocks_unauthorized_imports(mock_context):
    """Test that importing non-whitelisted modules (os) throws ImportError."""
    sandbox = BotSandbox()
    code = '''
import os
print(os.environ)
'''
    result = sandbox.execute(code, mock_context)
    assert result["success"] is False
    assert "Import os is restricted in this sandbox." in result["error"]

def test_sandbox_stops_infinite_loops(mock_context):
    """Test that a `while True` loop is killed after the defined timeout."""
    sandbox = BotSandbox()
    code = '''
while True:
    pass
'''
    # Override timeout to 1 second to make test fast
    result = sandbox.execute(code, mock_context, timeout=1)
    
    assert result["success"] is False
    assert "Bot execution exceeded timeout of 1s" in result["error"]
    assert result["duration_ms"] >= 1000

def test_sandbox_allows_context_variables(mock_context):
    """Test that input_resource, secrets, client, and event are injected correctly."""
    sandbox = BotSandbox()
    code = '''
print("Id =", input.get("id"))
print("Secret =", secrets.get("API_KEY"))
print("Action =", event.interaction)
'''
    result = sandbox.execute(code, mock_context)
    assert result["success"] is True
    
    log = mock_context.logger.get_log_output()
    assert "Id = 123" in log
    assert "Secret = supersecret" in log
    assert "Action = create" in log
