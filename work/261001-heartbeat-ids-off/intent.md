# Intent (accepted)

Status: accepted by Ty 01/10 ("approve 9", in chat). Found by this repo's new verification protocol (#8).

The runbook says the heartbeat names a source by file name only, never by a Drive file or folder id; the ids stay in the routine prompt. The 30/09 heartbeat in `data/.last-check` (tracked in this public repo, not served) carries two: the newest file's id and the source folder's id. Remove them.
