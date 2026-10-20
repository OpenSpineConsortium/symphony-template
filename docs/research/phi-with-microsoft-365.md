# Analyzing PHI with Symphony and Microsoft 365

Source: the thread "Outlook digest with one-touch decisions", 2026-10-20, from the owner's message of 17:38 UTC: the owner would like to analyze protected health information (PHI) with Symphony, and asked which OneDrive or other Microsoft features and permissions help. Read on the day: Anthropic's help center on business associate agreements ([privacy.claude.com, article 8114513](https://privacy.claude.com/en/articles/8114513-business-associate-agreements-baa-for-commercial-customers)), Wayne State's IRB policy 10-01 on HIPAA in research ([research.wayne.edu](https://research.wayne.edu/irb/aahrpp-policies-2024/10-01-hipaa-requirements-in-research-dua-update-administrative-update-102024.doc), title only, the text not read), and Microsoft's page on the de-identification service ([learn.microsoft.com](https://learn.microsoft.com/en-us/azure/healthcare-apis/deidentification/overview), through search results). What GitHub signs comes from third-party compliance sites only, so it waits on GitHub's own word. The rest is the author's knowledge, which needs checking before it is relied on. Nothing is legal advice. Every "may" below is a question for Wayne State's HIPAA privacy officer, the IRB and, where the data comes from Corewell Health, Corewell's data use agreement.

## The short answer

The owner's direction, 2026-10-20 17:44 UTC: Symphony analyzes PHI itself, with no part of it kept out. This note plans for that. Every place PHI passes through needs a business associate agreement (BAA) with whoever runs it, so making Symphony PHI-capable means running each of its parts where a BAA covers it. Microsoft covers most of it already. Three parts of today's Symphony have no BAA in the setup the owner uses, and each has a covered replacement:

| Part of Symphony | Today | No BAA because | Covered replacement |
|---|---|---|---|
| Repository, issues, pull requests, Actions | github.com | No source found says GitHub signs a BAA on any plan; third-party sources say its data protection agreement forbids PHI without GitHub's written consent | GitHub Enterprise Server run on the university's or the company's own Azure virtual machines, so the data sits on Azure under Microsoft's BAA and GitHub never holds it (inferred, to confirm with GitHub and Microsoft); or Azure DevOps, which Microsoft lists among its in-scope services (author's knowledge, to check) |
| Claude | A Max subscription token | Anthropic's BAA covers its first-party API and Enterprise plans once the Primary Owner turns HIPAA on and accepts it, and excludes Free, Pro, Max and Team, the Console and beta features | Claude Enterprise with HIPAA switched on, which Claude Code can sign in to; or Anthropic's API under the BAA; or Claude on AWS Bedrock, which is HIPAA eligible under AWS's BAA; or Claude in Microsoft Foundry, once Microsoft's BAA is confirmed to cover it |
| The sign-in Worker | Cloudflare Workers | Cloudflare signs a BAA only on Enterprise (author's knowledge) | Azure Functions under Microsoft's BAA, or Cloudflare Enterprise |
| Files, mail, calendar | OneDrive and Outlook through Graph | Covered: Microsoft 365 is in the BAA, if Wayne State allows PHI there | The same, inside a study's SharePoint site |
| Compute | Actions runners, the WSU grid | GitHub's runners are GitHub's; the grid's status for PHI is not known | Self-hosted runners on Azure under the BAA, or the grid once Wayne State approves it for PHI |

So a PHI-capable Symphony is the same code running on a covered stack: GitHub Enterprise Server and its runners on Azure, Claude under Anthropic's or a cloud's BAA, the Worker on Azure, and the files in Microsoft 365. Two project rules stand in the way, and both are the owner's to change for PHI. The first is "no API key, subscription tokens only": no subscription plan below Enterprise is covered. The second is "no server of ours": GitHub Enterprise Server is a server.

## Until the covered stack exists

Today's Symphony runs on github.com and a Max subscription, so PHI put into it now would sit outside any BAA. The drive organizer is the likeliest way in. It reads files into the GitHub branch drive-catalog (docs/memory/drive-organizer.md), so a PHI folder must stay out of the drive walk, Notebooks and the Folders tab's tracking until the covered stack is running. A guard that skips files whose sensitivity label marks PHI, read through Graph as below, would make that automatic. It is not built.

## What Microsoft offers

These need Wayne State's tenant to have the feature licensed and switched on. A university's A3 or A5 licence usually includes most of them (inferred).

- **The business associate agreement.** Microsoft's Product Terms include a HIPAA BAA for its in-scope services, among them Microsoft 365 (OneDrive, SharePoint, Exchange, Teams) and most of Azure. Whether a given storage place may hold PHI is still the university's decision. Several universities tell staff not to put PHI in OneDrive at all, for example the University of Washington. No page found on the day states Wayne State's own rule, so ask its HIPAA privacy officer.
- **A place made for PHI.** The usual way is a SharePoint site or a Teams team that IT sets up for one study. Sharing is limited to named people, outside sharing is off, and a sensitivity label is set as the default. A personal OneDrive is the weaker choice, since its owner can share from it freely.
- **Purview sensitivity labels.** A label such as "PHI - restricted" encrypts the file. The protection travels with the file wherever it goes, and the label can block printing, forwarding or download.
- **Purview data loss prevention.** Built-in detectors find US health and identity data, for example Social Security numbers, health insurance and Medicare numbers, and ICD codes. They can block a PHI file from being shared outside the university or sent out by email, and they warn the person who tries.
- **Audit, retention and eDiscovery.** Purview Audit records who opened which file. Retention keeps files as long as the study's record rules say. eDiscovery finds every copy when an auditor asks.
- **Conditional Access.** IT can let only managed devices, or only the university network, open the PHI site.
- **Azure Health Data Services**, under the same agreement:
  - the DICOM service stores imaging, such as spine MRI and CT, in the standard image format;
  - the FHIR service holds clinical records;
  - the de-identification service tags, redacts or replaces the HIPAA identifiers in free text.

  The de-identification service works on text, not image headers or text burned into images. Its own listing says it guarantees no Safe Harbor compliance, so a person still checks its output.
- **Azure compute and models.** Azure virtual machines, Azure Machine Learning and Azure OpenAI fall under the agreement. Claude is offered in Microsoft Foundry too, but whether Microsoft's BAA covers Claude there was not found on the day. AWS Bedrock, which also serves Claude, is HIPAA eligible under AWS's own agreement (author's knowledge).

## The Graph permissions that help

- **Sites.Selected (delegated or application).** The app reaches only the SharePoint sites an administrator names, not every file the person can see. This is the strongest fit for PHI: Symphony would be granted the study's site and nothing else, and IT can see exactly what it reaches. It needs admin consent, plus a second step in which IT grants each site.
- **Reading sensitivity labels.** Graph's extractSensitivityLabels on a file and the label definitions (InformationProtectionPolicy.Read) let Symphony see a file's label and skip it, which is the guard described above. They need admin consent.
- **Assigning labels.** Graph's assignSensitivityLabel on a file lets a workflow put the "PHI - restricted" label on its outputs. It is a metered API billed to an Azure subscription (author's knowledge, to be checked).
- **Not needed.** Files.Read.All, Mail.Read or any wide read. For PHI, the narrower the grant, the easier it is for IT and the IRB to approve.

## How the work would flow on the covered stack

1. The IRB approval and any Corewell data use agreement name where the data lives and who may touch it. The covered stack has to be on that list.
2. The data lives in the study's SharePoint site or in Azure (the DICOM service for images). Symphony reaches it through Sites.Selected, granted that site alone.
3. Claude, under the BAA, reads and analyzes the data the way it reads any repository today. Issues, pull requests, logs and results live on GitHub Enterprise Server inside Azure, so they may name patients if the study allows it.
4. De-identification remains available for what leaves the study, such as a paper, a CNS talk or a public repository. Safe Harbor's 18 identifiers come out of DICOM headers, burned-in text and free text, with Azure's de-identification service for text and a person checking the result.

## What waits on the owner

- Ask Wayne State's HIPAA privacy officer, and Corewell where its data is involved, which stack the study may use: Microsoft 365, Azure, GitHub Enterprise Server on Azure, and Claude Enterprise, the API, Bedrock or Foundry.
- Which Claude route to use for PHI. Claude Enterprise with HIPAA is the closest to today's way of working. Any of them changes the subscription-only rule for PHI work.
- Whether a GitHub Enterprise Server licence is affordable, or whether Azure DevOps is acceptable in its place. Either one changes the no-server rule for PHI work.
- Whether to build the label guard on the drive walk now, while Symphony still runs on github.com.
