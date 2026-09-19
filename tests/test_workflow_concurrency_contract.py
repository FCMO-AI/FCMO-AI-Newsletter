from __future__ import annotations

import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


class WorkflowConcurrencyContractTests(unittest.TestCase):
    def text(self,name: str) -> str:
        return (ROOT/".github"/"workflows"/name).read_text(encoding="utf-8")

    def assert_failed_workflow_run_isolated(self,name: str,group_prefix: str) -> None:
        text=self.text(name)
        self.assertIn("github.event_name == 'workflow_run'",text)
        self.assertIn("github.event.workflow_run.conclusion != 'success'",text)
        self.assertIn("github.run_id || 'active'",text)
        self.assertIn(group_prefix,text)
        self.assertIn("cancel-in-progress: true",text)

    def test_failed_bridge_event_cannot_cancel_active_refresh(self) -> None:
        self.assert_failed_workflow_run_isolated(
            "daily-refresh.yml","newsletter-refresh-v3-"
        )

    def test_failed_refresh_event_cannot_cancel_active_pages(self) -> None:
        self.assert_failed_workflow_run_isolated(
            "pages.yml","github-pages-v3-"
        )

    def test_pages_workflow_run_does_not_depend_on_optional_visibility_payload(self) -> None:
        text=self.text("pages.yml")
        self.assertNotIn("github.event.repository.visibility",text)
        self.assertIn(
            "github.event_name != 'workflow_run' || github.event.workflow_run.conclusion == 'success'",
            text,
        )
        self.assertIn("needs: build",text)
        self.assertIn("needs: deploy",text)


    def test_failed_deploy_event_cannot_cancel_real_health_check(self) -> None:
        self.assert_failed_workflow_run_isolated(
            "newsroom-health.yml","newsroom-production-health-v2-"
        )

    def test_refresh_promotion_retries_without_force_and_invalidates_on_product_inputs(self) -> None:
        text=self.text("daily-refresh.yml")
        self.assertIn("for attempt in 1 2 3 4 5",text)
        self.assertIn("BUILD_BASE=",text)
        self.assertIn("corpus scaffold tools .github/workflows/daily-refresh.yml",text)
        self.assertIn("newer product inputs",text)
        self.assertIn("retrying from newest main",text)
        self.assertIn("did not converge after 5 optimistic retries",text)
        self.assertNotIn("git push --force",text)
        self.assertNotIn("git push -f",text)



if __name__=="__main__":
    unittest.main()
