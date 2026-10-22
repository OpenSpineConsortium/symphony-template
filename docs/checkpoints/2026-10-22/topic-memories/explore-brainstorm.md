---
name: explore-brainstorm
description: Explore tab rebuilt 2026-10-21 as a dependency brainstorm canvas (Claude suggests links/tasks, push to native GitHub); what shipped and where
metadata:
  type: project
---
2026-10-21 greg approved ("yes finally you understand what i want") and it shipped: site #123 (Explore canvas, live), symphony-app #77 (checks BS1-BS11, 19 b* mutants), symphony-template #323 (assistant.md verbs `link #A blocks #B why ...` and `node TITLE under #E blocks #X after #Y why ...`, test pins them). Old tab hidden first (site #122, app #76). Design note: template docs/research/explore-dependency-brainstorm.md (#319).

Shape: one epic per chip; cards from the Dependencies tab's draw (state.graphLast); Claude's ideas from the assistant issue answer, dashed, Accept/Edit/Dismiss; Connect; Changes to push; Push writes as the person (issues todo -> sub_issues -> unlinks -> blocked_by by issue id), Undo closes new issues not_planned. Claude writes nothing. Not built: drag-to-connect, moving a task between epics.

**Why:** greg found the old Explore unintuitive; wants Claude-assisted planning that edits real tasks.
**How to apply:** owned by thread "Explore as dependency brainstorm"; JS block "Explore: plan an epic with Claude" in symphony-panel.js, CSS under #tab-explore; see [[native-first]], [[panel-checks-run]].
