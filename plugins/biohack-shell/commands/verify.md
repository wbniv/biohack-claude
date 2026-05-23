---
description: Run [verify] items from TODO.md — execute each plan's verification steps and record results in the plan file.
---
Scan `TODO.md` for items marked `[verify]` and run their verification steps.

For each `[verify]` item:

1. Find the linked plan file from the TODO item.
2. Open the plan and locate the verification/testing section.
3. Run each numbered verification step exactly as written.
4. Show the exact command run (as a `$ command` line) followed by raw output in a code block below each step.
5. Add a PASS/FAIL note after each step.
6. WRITE THE OUTPUT BACK INTO THE PLAN FILE — update the verification section with the raw output and PASS/FAIL under each step. The plan is the permanent record.
