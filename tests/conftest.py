import pytest

from agent_assurance import policy


@pytest.fixture(autouse=True)
def _reset_policy():
    """The active policy is process state; every test starts from defaults."""
    policy.reset()
    yield
    policy.reset()
