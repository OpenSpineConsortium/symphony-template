# Planning for scale: what Symphony would need if it grew large

Source: the thread "Outlook digest with one-touch decisions", 2026-10-20, from the owner's message of 17:14 UTC asking for a plan, made in advance, of what the owner may want if Symphony grows naturally into something the size of OpenAI. Nothing here is built or decided. The programme names and their requirements come from the author's knowledge of each vendor's documentation up to mid-2026 and were not read again this session, so each is to be checked against the vendor's own page before it is acted on. Where a line is a judgement and not a fact it says so.

## The short answer

At scale the hard parts are not technical. They are who owns Symphony (the company and Wayne State's claim on the owner's inventions), whose accounts the apps live under (today they live under the owner's personal accounts), the vendor reviews that every large platform puts in front of an app that reads people's mail and files, and the compliance work that a hospital, a university or an enterprise asks for before it signs. Most of these get cheaper the earlier they are settled. Six items are worth deciding before the user count grows, and the rest can wait for the stage that needs them.

## Decide now, while they are cheap

1. **Ownership and Wayne State's intellectual property policy.** A university's policy usually claims inventions that faculty make with university resources or in the course of their duties (inferred, and true of most US research universities; Wayne State's own policy is the one to read). Symphony was built on the owner's own accounts, but the WSU grid, the Wayne State tenant and any work time could all bring it under the policy. Ask Wayne State's Technology Commercialization office whether Symphony is the owner's or the university's. Keep this question separate from the spine-program provisional, which is confidential and is its own disclosure. The answer decides whether a company can own Symphony at all.
2. **A company to hold the apps.** SymphonyBoard, Symphony Setup and the Folders Entra app are registered under the owner's GitHub organization and the owner's personal Microsoft directory. An Entra app registration cannot be moved to another tenant. Moving one means a new registration, and everyone signs in and consents again, Wayne State's C&IT included. So any new app (the mail app, if it ends up separate) is best registered in the tenant that will own Symphony for good. That could be a company's own Microsoft 365 tenant, made once the company exists, rather than the owner's personal directory.
3. **The name.** "Symphony" is a crowded mark in software. GitHub already refused it as an App name because accounts exist under Symphony, Symph and Symph0ny, and Symphony is also the name of a well-known PHP framework and of a messaging company in finance (author's knowledge). Before money goes into the brand, a trademark search with a lawyer says whether Symphony can be registered for this use or needs another name. The rename tiers the project has already been through show what a late rename costs.
4. **PHI and the medical device rules are two separate questions.** Symphony analyzing PHI needs a business associate agreement for every part the PHI passes through. docs/research/phi-with-microsoft-365.md plans that covered stack (the owner's direction of 2026-10-20: Symphony handles PHI itself). Separately, software that helps a diagnosis on real patients, such as SchwingNet used clinically, falls under the FDA as software as a medical device, whatever it runs on. Research use under an IRB generally does not (inferred, a question for counsel when SchwingNet is clinical).
5. **Customers keep their own credentials.** The project already decided this: each customer's own Claude subscription, each contributor's own account, no pooled tokens. At scale it matters more, and two things follow. Running Claude on customers' behalf as a business needs Anthropic's commercial terms, not a consumer subscription's. And the owner's own account pool and orchestrator stay the owner's, never a product.
6. **A record of every decision and permission.** The repository already holds this record (CLAUDE.md, docs/research/, docs/memory/). At scale it becomes the evidence auditors ask for. Keeping it is cheap, and rebuilding it later is not.

## Stage by stage

### One owner and a few colleagues (now)

What exists covers it: the GitHub Apps, the Folders app with Wayne State's consent, the cloud sessions and the site. Still open: the Graph mail consent (docs/research/microsoft-365-permissions.md), the device permissions, which are each person's to grant (docs/research/device-permissions-for-a-person-like-claude.md), and the privacy statement, which the owner writes at release.

### A lab or a department (tens of people, several universities)

- **Microsoft.** A multi-tenant Entra app that people in other organizations sign in to needs publisher verification: a Microsoft AI Cloud Partner Program account in the company's name, linked to the app. Without it, most tenants block user consent to an unverified app, and every university's IT department sees a red "unverified" label. Each new university's IT department gives its own admin consent, as Wayne State's did, so docs/setup/folders-admin-consent.md becomes a template other IT departments can use.
- **Google**, if Google Drive or Gmail are offered. Drive and Gmail scopes beyond the narrowest are "restricted" or "sensitive". An app that asks for them for more than 100 users needs Google's OAuth verification, and a restricted scope adds a yearly security assessment by an approved lab (CASA).
- **GitHub.** The Apps' rate limit grows with the number of installations, but the board's and the coordinator's calls grow too. The board's reserve (the field-metrics budget) needs re-measuring at this size.
- **Universities' rules.** FERPA applies once student records pass through it, accessibility (WCAG 2.1 AA, and a VPAT, the form procurement asks for) comes in once a university buys it, and an IRB applies to any study of the people using it.

### A company with paying customers (hundreds of organizations)

- **Infrastructure.** The rule of "no server of ours" stops holding. A hosted webhook receiver, a database for customers' settings and a queue become cheaper than working around them. The design so far (stateless Workers, sealed tokens, Actions as compute) is the right start because it keeps customer data out of Symphony's hands. The rule to keep is "no customer secret at rest that a breach could leak", not "no server".
- **Security and compliance.** Enterprise buyers ask for SOC 2 Type II first: an audit over several months of how the company runs, not of the code. ISO 27001 matters in Europe. A penetration test comes once a year. Microsoft 365 App Compliance certification (Publisher Attestation, then Microsoft 365 Certification) matters to Microsoft-heavy buyers, and AppSource or Teams store listing needs it.
- **Enterprise features.** Single sign-on through SAML or OIDC, SCIM provisioning, audit logs, data retention controls, a choice of data region, and roles beyond "owner" all come in here.
- **Apps on phones and desktops.** An Apple Developer Program account in the company's name, App Store review with privacy labels, and Google Play's data safety form. A Microsoft Store listing and code signing certificates for Windows and macOS are needed too, so the installers are trusted.
- **Money.** A payment processor, sales tax and VAT handling, invoicing, and the GitHub Marketplace's verified-publisher process if the App is sold there.
- **Legal.** Terms of service, an acceptable use policy, a data processing agreement for GDPR customers, and a sub-processor list naming Anthropic, GitHub, Cloudflare and Microsoft. The licence choice the project already made (MIT for the protocol and plugin, possibly ELv2 or BSL for the runtime) needs a lawyer's reading before the first customer.

### Very large (millions of people)

This is a judgement about what the stage would bring, not a measurement:

- **Your own models or a deep partnership.** At this size, depending on one model vendor's consumer subscriptions is the largest risk. Either a commercial agreement with Anthropic at volume or a way to serve models of the company's own becomes necessary. That is where a company like OpenAI's spending goes.
- **Trust and safety.** Abuse detection, a team for reports, transparency reports, and, under the EU AI Act, obligations for general-purpose AI systems and for any high-risk use (education and employment are listed as high risk).
- **Regulators by sector.** In health, FDA rules for any clinical feature and HIPAA for the data. In education, FERPA and each country's own rules. In government, FedRAMP for US agencies. In finance, the banking regulators' vendor reviews.
- **Data and people.** A security team on call, incident response, a bug bounty, regional data centres, and export controls on models and encryption.

## Permissions that grow with it

The permission side the owner has asked about so far, gathered in one place:

- **Microsoft Graph.** Now: Files and, soon, Mail. Later Calendars, Tasks, Teams and OneNote, as docs/research/microsoft-365-permissions.md phases them. At scale: application permissions under each customer's admin consent for background work, which Microsoft reviews more strictly than delegated ones.
- **Google Workspace**, if offered: Drive, Gmail and Calendar, each behind verification and, for restricted scopes, the yearly assessment.
- **GitHub.** The two Apps as now. At scale, perhaps a GitHub Marketplace listing and GitHub's partner programme.
- **Devices.** Camera, microphone, biometrics, Bluetooth and VR, granted by each person on each device, never by an IT department (docs/research/device-permissions-for-a-person-like-claude.md).
- **Health data**, only in a separate clinical product: Apple HealthKit, Health Connect on Android, and a hospital's EHR through FHIR and SMART on FHIR. Each brings HIPAA, and the EHR vendors' app reviews too.

## What waits on the owner

- Asking Wayne State's Technology Commercialization office whether Symphony is the owner's or the university's.
- Whether to make a company now or later, and so where new apps are registered from now on.
- A trademark search on the name Symphony.
- Which of the stages above the owner wants to aim for first. This note recommends the lab or department stage, since the Wayne State consent work already rehearses it.
