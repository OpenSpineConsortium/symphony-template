# Ownership

Which account owns which area of the repository. Any account claims issues anywhere, but a pull request that touches an area another account owns asks that account for a look, and the coordinator routine flags two open pull requests that touch the same files. The repository owner merges everything: .github/CODEOWNERS names {{OWNER}}.

| Area | Paths | Account | Label | Merges |
| --- | --- | --- | --- | --- |
| The whole repository, until areas are split | everything | main | account:main | {{OWNER}} |

To split an area: add a row with its paths, the account and the account's label (docs/setup/github.md says how to add one), by pull request, and say so in docs/project.md under Owners.
