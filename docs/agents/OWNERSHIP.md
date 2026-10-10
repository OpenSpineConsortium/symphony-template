# Ownership

Which account owns which area of the repository. Any account claims issues anywhere, but a pull request that touches an area another account owns asks that account for a look, and the coordinator routine flags two open pull requests that touch the same files. The repository owner merges everything, and .github/CODEOWNERS asks {{CODE_OWNER}} to review every pull request: the owner's own login, or in an organization's copy the person who made the copy, since GitHub asks a user or a team for review and never an organization (docs/setup/github.md, section 7).

| Area | Paths | Account | Label | Merges |
| --- | --- | --- | --- | --- |
| The whole repository, until areas are split | everything | main | account:main | {{CODE_OWNER}} |

To split an area: add a row with its paths, the account and the account's label (docs/setup/github.md says how to add one), by pull request, and say so in docs/project.md under Owners.
