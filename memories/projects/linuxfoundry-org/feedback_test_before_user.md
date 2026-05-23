---
name: feedback_test_before_user
description: Always test API calls and scripts locally before asking the user to run them
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 98581e12-5331-42f2-81b3-9c1dc824689c
---

Never send the user a script or API call to run without first testing it yourself. If credentials are available in /tmp/foundry-linux-bootstrap.env or the environment, use them to run the actual API call and verify the response before committing.

**Why:** User had to run bootstrap.sh multiple times through repeated failures (jq syntax errors, wrong API phase, 400/405 errors) that were entirely diagnosable locally with the cached credentials.

**How to apply:**
- Check /tmp/foundry-linux-bootstrap.env for cached CF_API_TOKEN
- CF_ZONE_ID and CF_ACCOUNT_ID are visible in earlier session output
- Run curl API calls directly to verify shape of response before wiring into bootstrap.sh
- Only commit once the API call returns success locally
