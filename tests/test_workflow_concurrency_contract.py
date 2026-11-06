from __future__ import annotations

import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


class WorkflowConcurrencyContractTests(unittest.TestCase):
    def text(self,name: str) -> str:
        return (ROOT/".github"/"workflows"/name).read_text(encoding="utf-8")

    def assert_failed_workflow_run_isolated(self,name: str,group_prefix: str,
                                            cancel: str="cancel-in-progress: true") -> None:
        text=self.text(name)
        self.assertIn("github.event_name == 'workflow_run'",text)
        self.assertIn("github.event.workflow_run.conclusion != 'success'",text)
        self.assertIn("github.run_id || 'active'",text)
        self.assertIn(group_prefix,text)
        self.assertIn(cancel,text)

    def test_failed_bridge_event_cannot_cancel_active_refresh(self) -> None:
        # Automatic refreshes queue on the 'active' lease (cancelling the run in
        # flight starved every refresh once the pre-push guard made a rebuild
        # longer than the trigger interval); only a manual dispatch pre-empts.
        self.assert_failed_workflow_run_isolated(
            "daily-refresh.yml","newsletter-refresh-v3-",
            "cancel-in-progress: ${{ github.event_name == 'workflow_dispatch' }}",
        )
        self.assertNotIn("cancel-in-progress: true",self.text("daily-refresh.yml"))

    def test_failed_refresh_event_cannot_cancel_active_pages(self) -> None:
        # Pages queues automatic runs on the 'active' lease (cancelling them
        # starved every deploy); only a manual main dispatch pre-empts.
        self.assert_failed_workflow_run_isolated(
            "pages.yml","github-pages-v4-",
            "cancel-in-progress: ${{ github.event_name == 'workflow_dispatch' }}",
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

    def test_refresh_promotion_retries_without_force_and_invalidates_on_constructor_inputs(self) -> None:
        from tools import refresh_promote
        text=self.text("daily-refresh.yml")
        self.assertIn("BUILD_BASE=",text)
        self.assertIn('python3 tools/refresh_promote.py --build-base "$BUILD_BASE"',text)
        self.assertEqual(refresh_promote.CONSTRUCTOR,
                         ("scaffold", "tools", ".github/workflows/daily-refresh.yml"))
        helper=(ROOT/"tools/refresh_promote.py").read_text(encoding="utf-8")
        self.assertIn("for attempt in range(1, 6)",helper)
        self.assertIn("descartado por constructor",helper)
        self.assertIn("reintentando desde el main más nuevo",helper)
        self.assertIn("no convergió tras 5 reintentos",helper)
        self.assertIn('["git", "push", "origin", f"{head}:refs/heads/main"]',helper)
        for code in (text,helper):
            self.assertNotIn("git push --force",code)
            self.assertNotIn("git push -f",code)



if __name__=="__main__":
    unittest.main()
