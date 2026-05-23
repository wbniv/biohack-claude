# Memory index

- [/new-web-apt-repo skill reuse](project_new-web-apt-repo-skill.md) — skill is generic; user plans to reuse it for WorldFoundry APT repo setup
- [task bump for releases](feedback_task_bump.md) — use `task bump` to sync+release foundry-apt; auto-increments patch version, no TAG needed
- [read prompt blank-input guard](feedback_read_prompts.md) — always wrap `read` in an until loop; blank Enter must never silently set an empty variable
- [test API calls locally before user runs](feedback_test_before_user.md) — use cached credentials in /tmp/foundry-linux-bootstrap.env to test CF API calls yourself first
