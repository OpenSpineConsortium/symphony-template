# Forming a company to hold Symphony: a Michigan LLC and Wayne State's policy

Source: the thread "Forming an LLC", 2026-10-22, the owner's ask "It's time to create an llc". Not legal advice; every point marked for a lawyer is one. The owner's private plan and draft operating agreement are in the Project's files under llc/ and stay out of every repository, as anything about an invention disclosure does. This note follows planning-for-scale.md, whose first two items (Wayne State's claim, a company to hold the apps) it answers in part.

## Wayne State's statute, read

Board of Governors Statute 2.41.04, Patent and Copyright Policy (https://bog.wayne.edu/code/2-41-04, adopted 1969, amended 1984), read on 2026-10-22:

- Copyright: faculty and staff "retain all rights to copyright in published works"; the university may publish without copyright, or hold it, only for a work an employee was directed to produce within the scope of employment. The patent policy "applies only to patentable inventions"; software is not named. So the copyright in Symphony's published code reads as its author's, which a company can be assigned. A lawyer confirms that self-directed, published software is a "published work" and that no departmental term adds to it.
- Patents: the inventor owns an invention made without university support, or without university funds (salary excepted), facilities, equipment or services and free of any sponsor's terms. Otherwise the university has the right of first refusal to title and decides within four months to take or waive it; if it takes title and does not license within 24 months of the patent issuing, ownership passes to the inventor. Symphony's patentable mechanisms touched the WSU grid and the Wayne State tenant, so who owns any patent on them is the question for Technology Commercialization that planning-for-scale.md already names.
- Whether rights have already passed depends on the wording of the University Patent Agreement an employee signs, not on the statute alone: "hereby assign" transfers future inventions at once, "agree to assign" is a promise that leaves title with the inventor until an assignment is signed (Board of Trustees of Leland Stanford Junior University v. Roche Molecular Systems, 563 U.S. 776 (2011)). A lawyer reads the signed agreement.
- The consulting waiver is refused where the faculty member is a stockholder or officer of the company, so a company of the owner's own takes university-owned technology by licence, which the Board approves in open session by two thirds after the employee's interest is disclosed, as for Mitovation, Inc. on 2024-10-24 (https://bog.wayne.edu/meetings/390/23-24-oct-2024-bog-agenda-item-viiic.pdf).

## Which state

Michigan: Articles of Organization (form CSCL/CD-700) for $50 through the MiBusiness Registry (https://www.michigan.gov/corpfileonline), an annual statement of $25 due each 15 February, none the first February for a company formed after 30 September (https://www.michigan.gov/lara/bureau-list/cscl/corps/frequently-asked-questions), and the owner may be his own registered agent. Delaware ($110 to form, $300 a year) or Wyoming ($100, $60 a year) would each also have to register in Michigan as a foreign LLC, where the owner works, adding a second set of fees and a paid agent; Delaware matters for venture investors, who ask for a C-corporation in any case. Recommended: Michigan, converting later if investment comes.

## Steps that need no lawyer

Name check (https://www.michigan.gov/corpentitysearch and https://tmsearch.uspto.gov), the filing, a free EIN from the IRS, an operating agreement, a business bank account. FinCEN's beneficial-ownership report no longer applies to US-formed companies since its March 2025 rule.

## What it changes for Symphony

An Entra app registration cannot change tenant (planning-for-scale.md), so a company's own Microsoft 365 tenant, made once the company exists, is where any new Entra app belongs; the GitHub organization needs no move, since an organization's owners can act for the company, and a GitHub App can be transferred between accounts without being registered again. Publisher verification for the Entra apps, an Apple or Google developer account and a trademark filing are each made in the company's name.
