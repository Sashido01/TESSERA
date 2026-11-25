# Git Inspector — stage II candidate

[Русский — оригинал](GIT_INSPECTOR.md) | **English — translation**

`python scripts/git_inspector.py --root <project-root>` observes HEAD (including unborn/detached), changed, conflicted and untracked path counts, local branches, annotated and other tags, and remote count. No GitHub or network needed. Does not output paths, branch names or remote URLs. Two successive status/refs/remote-name observations detect some changes: OBSERVED means matching observations, STALE means difference (exit 1); Git/input error exits 2. Status and refs SHA-256 values are observation digests, not content hashes or atomic snapshots. Counting annotated tags does not verify releases.

Use only a trusted stable checkout, installed Git and authorized command. Git status may read contents and invoke locally configured filters; this is not a sandbox. Inherited GIT_* variables are excluded, optional locks, fsmonitor and global/system config disabled, lazy fetch prohibited in supporting Git. No network commands invoked. Does not inspect submodule worktrees, ignored files, contents, remote refs or changes reverted between observations. 15 seconds per command, 4 MiB after capture, not a hard memory or descendant-process bound. Not proof of security or full project cleanliness. Local Linux tests 13/13; Windows and CI NOT_VERIFIED.
