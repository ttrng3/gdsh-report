# Intent (accepted)

Status: accepted by Ty 02/10 (his conditions for this fix, confirmed with "yes, go", in chat).

The verifier run on 02/10 failed step 4 of `verification/report-pages.md` on a correct preview: the publisher wraps the fragment in a fixed page skeleton, so a whole-page hash can never equal the build's. Strip only that skeleton before comparing, without loosening the check in any other way, and prove the step can still fail.
