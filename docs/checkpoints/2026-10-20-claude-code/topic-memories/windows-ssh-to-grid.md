---
name: windows-ssh-to-grid
description: "Windows OpenSSH 9.5 reaches warrior only with `MACs +hmac-sha1`, and takes 13 s per connection unless `AddressFamily inet` (IPv6 timeout); the Ashley block in %USERPROFILE%\\.ssh\\config (alias wsu-grid, also `grid`) and key id_ed25519_wsu now exist on Windows and WSL"
metadata:
  node_type: memory
  type: reference
  originSessionId: 0599380b-0d32-4e19-b5be-65bdd1017566
  modified: 2026-09-28T00:47:01.458Z
---

Measured 2026-09-28: `ssh go2432@warrior.grid.wayne.edu` from Windows fails with "no matching MAC found.
Their offer: hmac-sha1" unless `-o MACs=+hmac-sha1` (WSU's own generator adds it). With it, every connection
took 13.1 s; the delay is before "Connecting to ... [141.217.136.64]", i.e. an IPv6 attempt; `-o
AddressFamily=inet` brings it to 2.0 s (nine runs). `GSSAPIAuthentication=no` alone changes nothing.

Ashley's wizard wrote the managed block to `C:\Users\grego\.ssh\config` (Host `wsu-grid grid`, `Host
*.nas.grid.wayne.edu` with ProxyJump) and mirrored key + config into WSL, so `ssh grid` now resolves in both
(supersedes the note in [[grid-access]] that `grid` did not resolve). Windows key:
`~/.ssh/id_ed25519_wsu`, authorized on the grid (comment "ashley-windows").

**How to apply:** from Windows, `ssh wsu-grid ...` works in PowerShell/Git Bash without WSL; keep WSL for
git push/HF (Windows socket flakes, [[wsl-for-network]]). Remote-SSH host for a node: `<node>.nas.grid.wayne.edu`.
