What each GitHub and Claude plan unlocks for this template; verified 2026-10-09, details and sources in docs/setup/tiers.md.

A public repository makes GitHub free outright: unlimited Actions on
standard runners and enforced branch protection and rulesets on the
Free plan. A private one gets 2,000 included minutes on Free and
enforcement only from Pro ($4, personal), Team or Enterprise; with no
payment method stored, the quota is a hard stop, never a bill. Pro and
Team both include 3,000 minutes; Enterprise Cloud 50,000. Push
restrictions and bypass lists exist only for organizations (Team and
up on private repositories), so below Team the push-guard hook and the
protocol check are the only fences. Claude Code comes with every paid
Claude plan on the one usage pool (five-hour window plus weekly limit):
Pro $17-20, Max $100/$200 monthly (more usage, no new features), Team
$20-25 a seat with Claude Code on every seat. `claude setup-token`
works from Pro up, so the @claude and worker workflows need only the
cheapest paid plan. The API credits bundled with Max and Team are
Console-side only and never extend Claude Code. Keep CI on ubuntu
runners: Windows bills at about 1.7x, macOS at about 10x.
