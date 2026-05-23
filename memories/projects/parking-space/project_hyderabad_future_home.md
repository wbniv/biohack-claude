---
name: Hyderabad is the preferred future infra home
description: Why ap-south-2 (Hyderabad) is the target region for project infrastructure once it reaches feature parity with ap-south-1 (Mumbai)
type: project
originSessionId: 03c2113f-f3d3-4b81-bd59-6e39e564609b
---
Current project infrastructure (build, monitoring, bastion) is in **Mumbai (ap-south-1)**. The preferred future home is **Hyderabad (ap-south-2)**.

**Why:** Same S3 storage price as Mumbai ($0.025/GB-mo) and same cross-region/internet egress ($0.086/GB cross-region, $0.109/GB to internet), but **lower ping times** for project operators. No cost delta, just latency.

**How to apply:** When ap-south-2 gains feature parity with ap-south-1 on the services this project uses (currently a blocker — e.g. some S3 / networking / launch-template capabilities), migrate the Mumbai infrastructure to Hyderabad. For any plan that involves choosing an Indian region now, pick Mumbai (feature-complete) but note Hyderabad as the target; for plans designed years out, assume Hyderabad. Do not pay a cost premium or accept feature gaps just to land in Hyderabad sooner.

Bangkok (ap-southeast-7) remains the app primary region — unrelated to this infra-home choice.
