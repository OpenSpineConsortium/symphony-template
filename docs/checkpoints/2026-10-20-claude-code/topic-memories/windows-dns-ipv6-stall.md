---
name: windows-dns-ipv6-stall
description: Why Windows network calls to GitHub take 11-20 s -- the IPv6 (AAAA) DNS lookup stalls ~11 s before IPv4 is used; curl -4 answers in 0.16 s; the ssh fix was AddressFamily inet; WSL has no stall
metadata:
  type: reference
---

Measured 2026-10-11 from git-bash on Windows: `curl https://api.github.com/` total 11.25 s with dns 11.12 s; `curl -4` total 0.16 s with dns 0.02 s. `git ls-remote` over https takes 20 s per call (two lookups), `gh.exe api user` 12 s; `git ls-remote --ipv4` fails (ls-remote has no such flag; fetch/push/clone do). This is the "Windows sockets flake" of [[wsl-for-network]]: not socket loss but an AAAA lookup that waits out a timeout on every connection. The ssh cure was `AddressFamily inet` ([[windows-ssh-to-grid]]). For https there is no git/gh config to force IPv4, so network-heavy work (pushes, gh, headless claim sessions) runs in WSL, which has no stall. A Windows-level fix (resolver / IPv6 setting) is Greg's decision; not applied.
