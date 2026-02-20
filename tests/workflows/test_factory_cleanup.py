from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import Mock

from dslighting.workflows.factory.base import BaseWorkflowFactory


class _DummyFactory(BaseWorkflowFactory):
    def create_workflow(self, config, benchmark=None):
        raise NotImplementedError


def test_cleanup_uses_last_runner_workspace_service() -> None:
    factory = _DummyFactory(keep_workspace=False)
    runner_workspace = Mock()
    factory._last_runner = SimpleNamespace(workspace_service=runner_workspace)

    factory.cleanup()

    runner_workspace.cleanup.assert_called_once()


def test_cleanup_falls_back_to_factory_workspace_service() -> None:
    factory = _DummyFactory(keep_workspace=False)
    fallback_workspace = Mock()
    factory.workspace_service = fallback_workspace

    factory.cleanup()

    fallback_workspace.cleanup.assert_called_once()


def test_cleanup_skipped_when_keep_workspace_true() -> None:
    factory = _DummyFactory(keep_workspace=True)
    workspace = Mock()
    factory.workspace_service = workspace
    factory._last_runner = SimpleNamespace(workspace_service=workspace)

    factory.cleanup()

    workspace.cleanup.assert_not_called()
