---
name: grid-ssh-second-factor
description: How ssh sign-in to the WSU grid works from outside the VPN (password + Google Authenticator TOTP, enrolled in OnDemand's 2FA Setup app; keys skip it), read on warrior 2026-10-01
metadata:
  type: reference
---

Read on the grid login node (warrior) on 2026-10-01. `grid.wayne.edu:22` answers from the internet without the VPN (OpenSSH 7.4; host key RSA only, SHA256:kLTz1xK6anQ1denM+31kDEryQtgan2P76r9aLno+K3s; ciphers aes-ctr only; MAC hmac-sha1 only; methods publickey, password, keyboard-interactive).

`/etc/pam.d/password-auth` (used by sshd): `pam_sss` for the university password, then `pam_google_authenticator.so` with the prompt "Your google authenticator one-time verification code: ", then `pam_echo` of `/usr/local/bin/setupgoogleinstructions.txt`, then deny. That file says: "You either typed in the wrong code, or you do not have Google Authenticator 2FA setup. Please try again, or login to OnDemand and run the 2FA Setup app", tutorial https://tech.wayne.edu/kb/high-performance-computing/hpc-tutorials/500195.

So: the second factor is TOTP (Google Authenticator), enrolled through OnDemand's own "2FA Setup app" on the VPN (that is where the QR code appears, not in a first ssh session). A student without it cannot sign in by ssh password at all. A key sign-in skips both password and code (Greg's does). `duo_unix` is installed but not in the stack as read. The OnDemand server reaches warrior from 10.3.136.24. OnDemand itself signs in with HTTP Basic, see [[ashley-bridge-project]].

The login node's notice bans by name, "terminated on sight": python, python2, python3, node, pip, md5sum, rsync, conda, gcc, make, R and others. The cluster tool `hpcworker` runs the system python3 briefly on the login node: a rule problem to fix (make the login-node path bash-only). Related: [[no-jobs-on-login-node]], [[beethoven-first-run-ux]].
