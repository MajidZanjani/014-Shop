# Repository protection proposal — review only

No GitHub access, repository ruleset, branch protection or runner access changed. Existing manual full qualification remains mandatory and separate from ordinary development checks.

For repository-owner review: protect main against deletion/force-push; require current ordinary development `catalog-frontend` and `backend-worker` results before merging; require review of approval/identity/payment/archive/dependency/host-protection changes. Exact required GitHub check context names must be taken from actual completed runs before applying policy. Keep failed/cancelled/skipped/zero-case checks blocking, with no substitute green placeholder for an unassigned qualification runner.

Release approval additionally requires the existing full qualification workflow's actual independent assigned-runner results plus commercial/provider/security/retention/restore/host-specific gates. A successful ordinary hosted run does not satisfy that boundary. Assigned-runner access, repository policy mutations and live activation require their own existing scoped authority; this file proposes no automatic change and contains no credentials.
