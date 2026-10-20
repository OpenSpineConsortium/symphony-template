---
name: ashley-compliance-boundary
description: "The design boundary Ashley must stay inside (from the 2026-09-28 terms-of-service research): Ashley never handles a Claude credential; each student signs in through Claude Code's own flow on laptop and grid; automation on the vendor's own accounts only; the exposures no EULA removes"
metadata:
  node_type: memory
  type: project
  originSessionId: 0599380b-0d32-4e19-b5be-65bdd1017566
  modified: 2026-09-28T14:57:48.425Z
---

**Binding constraint (Anthropic, Claude Code legal page, read 2026-09-28):** third-party developers
"may not collect, store, or intermediate Claude.ai credentials or session tokens" and may not route
requests through Pro/Max credentials on users' behalf; the carve-out is an end user "signing in to
the unmodified Claude Code binary with their own Claude subscription, including where a platform
hosts Claude Code". Enforcement since April 2026 falls on students' subscriptions.

**What Ashley therefore does (v2.0.0, grid scripts v4):** no setup-token capture, storage or copy.
The student runs `ashley claude login` (the extension opens the terminal) = `claude auth login`
inside their own Slurm allocation in the lab container; Claude Code stores its credential in
`~/.ashley/claude`; every Claude Code process Ashley starts gets `CLAUDE_CONFIG_DIR` there and an
env with all six credential vars removed. The daemon reads only `claude auth status` (heartbeat
`claude_login`). One person, one account; the only fallback is the student's own Console key.
Remote Control uses the same login; the student answers "Enable Remote Control?" themselves
(`ashley claude remote-consent`, marker file). Ashley never runs `claude auth logout`.

**Still open, in writing, before any paid key:** Anthropic sales on the orchestration pattern
(`docs/ANTHROPIC_REQUEST.md` is the draft); WSU Office for Technology Commercialization on ownership
(BOG 2.41.04, "University support", app-store release = public disclosure); counsel on the licensor
entity (LICENSE.txt names Gregory Schwing trading as OpenSpineConsortium; an LLC was recommended) and
on the Tenet Code of Conduct clause. Move commercial build/test off the Grid (UP 00-1 sec. 3.3). The
extension id dropped "wsu" (APPM 10.12). A Michigan EULA cannot waive the MCPA or bind third
parties; no DMCA 1201 help for a key check in readable JavaScript (Lexmark, 6th Cir.).

**Disputes (second report, 2026-09-28, `Ashley liability shield and Marketplace`):** no clause blocks
suits at inception; the set that holds is notice-and-cure, individual arbitration + class waiver +
delegation (Concepcion, StockX) with a 30-day opt-out, small-claims and public-injunction carve-outs,
jury waiver, one-year limit (Rayford 2025 reasonableness test), conspicuous disclaimers/caps, specific
consent per MCPA 445.903(1)(t), no review restrictions (CRFA). Costs: AAA consumer arbitration is
about $3,275 per claim on the business; mass-arbitration batching is the weakest clause (Heckman
2024). Assent = un-prechecked checkbox naming the button + typed name + stored version/hash/texts
(UETA 450.838(3)). Structural: LLC ($50), tech E&O (~$400-1,800/yr), copyright registration,
Michigan 6% sales tax on downloaded software, EAR mass-market self-classification (bundled ssh2).
Marketplace: removal "for any reason"; disclosure of what the extension does at the top of README and
description; privacy policy mandatory; minified-not-obfuscated has been removed before (nuBond);
no eval/dynamic require; verified domain needs six months. Greg said he assumes the risk; the notice
address on the support page is still a placeholder.

**Why:** Greg asked for the exact narrow space and minimal concessions; the research report is
`ashley/docs/research/reports/Ashley terms of service constraints.md` (23-clause spec, 18 exposures).

**How to apply:** any feature that would read, cache, relay or refresh a Claude credential, run work
on a student's Claude account for the vendor's benefit, or run a process on the login node is out.
The maintenance pipeline runs on Greg's own Console key (`.github/workflows/triage.yml`). Related:
[[ashley-extension-project]], [[commercialization-stance]], [[diagnostics-graph-required]].

**Shipped 2026-09-28 (terms version 3):** courts, not arbitration. Section 19 = signed 60-day
notice-and-cure as a condition precedent, Wayne County / E.D. Mich. with small claims where the
student lives, stand-alone severable class waiver, one-year limit for contract and warranty claims
only, mutual reasonable fees; section 20 = separately headed jury waiver; cap = greater of 12
months' fees or $100; 14-day refund on request; E-SIGN consent; state riders NJ/CA/TX/MA. Reason:
the AAA per-claim floor (~$3,275) exceeds the MCPA class ceiling at a few hundred licenses, and
batching protocols are the clause courts strike. The arbitration text and the threshold for
adopting it are in `docs/legal/ARBITRATION_OPTION.md`; adopting it means a `TERMS_VERSION` bump and
re-acceptance. The dialog button is "Accept and Continue"; the four checkbox labels are recorded
verbatim in the acceptance record; opening the text in an editor counts as reading it.
