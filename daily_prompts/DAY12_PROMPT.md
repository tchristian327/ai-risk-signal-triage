# Claude Code prompt — Day 12: Infrastructure as Code with AWS CDK

Before writing any code, re-read `CLAUDE.md` and `DECISIONS.md` in full. Read `PLAN.md` at the section for Day 12. Then, in your own words, give me a 3-4 sentence summary of what we're building today, why CDK in Python (not Terraform), and what the deployed stack contains. Do not skip this step.

Once I confirm the summary, your task for Day 12 is to provision the project's AWS resources using AWS CDK in Python. The goal is a minimal but real IaC stack that an interviewer can see was actually deployed, not just written.

## Prerequisites

Confirm these exist before starting:
- A working pipeline that runs end-to-end (from Day 4+)
- AWS credentials configured locally with permissions for CloudFormation, IAM, S3, and Bedrock
- `aws-cdk-lib` is listed in the CLAUDE.md tech stack (added during planning)
- Day 11 is complete (observability, Docker, CI all in place)

If Day 11 is not complete, stop and finish it first. Day 12 depends on the production hygiene pass being done.

## What to build

1. **Create the `infra/` folder** at the project root with a minimal CDK app in Python:

   ```
   infra/
   ├── app.py              # CDK app entry point
   ├── stacks/
   │   └── risk_agent_stack.py  # The single stack
   ├── cdk.json
   └── requirements.txt    # CDK-specific deps (aws-cdk-lib, constructs)
   ```

   Use `aws-cdk-lib` (CDK v2). Do not use CDK v1 or any legacy construct libraries.

2. **Build the stack in `infra/stacks/risk_agent_stack.py`** with two resources:

   a. **An IAM role with a Bedrock invoke policy.** The role should grant `bedrock:InvokeModel` and `bedrock:InvokeModelWithResponseStream` for the specific Claude model ARN used by the scorer. Import the `BEDROCK_MODEL_ID` constant from `src/scoring.py` rather than hardcoding the model ID string — this keeps the IAM policy and the scorer referencing the same single source of truth. Scope the policy to the specific model, not `bedrock:*`. Add a trust policy that allows the role to be assumed by the AWS account root principal. Note: in this portfolio project the role is provisioned to demonstrate the least-privilege Bedrock access pattern and is not actively assumed by the pipeline at runtime — the pipeline uses local IAM user credentials directly. Document this clearly in `infra/README.md` so anyone reading the stack understands the role's purpose.

   b. **An S3 bucket for pipeline run artifacts.** This stores `digest.json` and `run_metadata.json` from each pipeline run. Settings: versioning enabled, public access blocked (all four block settings), server-side encryption with S3-managed keys (SSE-S3). Add a lifecycle rule that transitions objects to Infrequent Access after 30 days. Use a removal policy of RETAIN (don't delete the bucket if the stack is destroyed).

   Add tags to both resources: `Project: ai-risk-signal-triage`, `Environment: dev`, `ManagedBy: cdk`.

3. **Configure `cdk.json`** with the app entry point pointing to `infra/app.py`. Set the CDK context for the target AWS account and region (read from environment variables, with sensible defaults matching `.env.example`).

4. **Create `infra/requirements.txt`** with:
   ```
   aws-cdk-lib>=2.100.0
   constructs>=10.0.0
   ```

5. **Create `infra/README.md`** explaining:
   - What the stack provisions (IAM role + S3 bucket)
   - How to install CDK dependencies (`pip install -r infra/requirements.txt`)
   - How to synthesize (`cd infra && cdk synth`)
   - How to deploy (`cd infra && cdk deploy`)
   - How to destroy (`cd infra && cdk destroy`)
   - A note that the S3 bucket has RETAIN policy and must be manually deleted if the stack is destroyed
   - A note that the IAM role is provisioned to demonstrate least-privilege Bedrock access patterns and is not actively assumed by the pipeline (the pipeline uses local IAM user credentials directly)

6. **Deploy the stack.** Run `cdk synth` to verify the template is valid, then `cdk deploy` against the real AWS account. This is a real deployment, not a dry run.

7. **Take a screenshot** of the deployed CloudFormation stack in the AWS console showing the stack status and resources. Save to `docs/screenshots/cloudformation_stack.png`.

8. **Update the main README.** Add a short "Infrastructure" section (3-4 sentences) that mentions the CDK stack, what it provisions, and references the screenshot. Place it after the "Tech stack" section.

9. **Update `DECISIONS.md`** with an entry explaining:
   - Why CDK in Python (same language as the rest of the project, avoids context-switching to HCL)
   - Why these two resources specifically (IAM for least-privilege Bedrock access, S3 for artifact persistence)
   - Why the pipeline is not rewired to use these resources yet (that would be production work beyond the portfolio scope)

## Implementation notes

- **The pipeline does not need to be rewired.** The CDK stack provisions resources that the pipeline *could* use, but we don't need to modify `src/pipeline.py` to upload to S3 or assume the IAM role. Having the infrastructure deployed and documented is enough for the interview signal. If time permits, adding an `--upload-to-s3` flag to the pipeline is a clean follow-up, but it's not required.

- **Keep the stack minimal.** Two resources. No VPC, no Lambda, no API Gateway, no ECS. The point is to show the IaC pattern exists and works, not to build a full cloud architecture.

- **CDK bootstrapping.** If the AWS account hasn't been CDK-bootstrapped yet, run `cdk bootstrap` first. Document this in `infra/README.md`.

- **No secrets in the CDK code.** The account ID and region come from environment variables or the CDK CLI context, not hardcoded values.

- **Type hints and comments.** Same conventions as the rest of the project. The CDK code should be readable to someone who knows Python but not CDK.

## Definition of done

- `cd infra && cdk synth` produces a valid CloudFormation template without errors
- `cdk deploy` has been run successfully at least once against the real AWS account
- The CloudFormation stack screenshot is in `docs/screenshots/`
- `infra/README.md` explains how to synth, deploy, and destroy
- The main README references the IaC work
- `DECISIONS.md` has the CDK rationale entry
- The pipeline still runs end-to-end without changes (the CDK work is additive, not disruptive)

## Scope guardrails

- **Do not** rewire the pipeline to use the CDK-provisioned resources unless time is abundant and the rest of the day's work is done
- **Do not** add Lambda, API Gateway, ECS, or any compute resources. This is storage and IAM only.
- **Do not** add a custom domain, CloudFront, or any networking resources
- **Do not** modify the scoring logic, the eval set, or the dashboard
- **Do not** add Terraform, SAM, or any other IaC tool. CDK only.
- **Do not** start Day 13 work (LangGraph) on this day

## Skills to load

None. CDK work is straightforward infrastructure code. If you're unsure about CDK patterns, check the AWS CDK v2 Python docs before guessing.

When you're done, give me a short summary of: (1) what resources the stack provisions, (2) the `cdk synth` output (just confirmation it worked), (3) the `cdk deploy` result, (4) the screenshot location, and (5) any concerns about Day 13.
