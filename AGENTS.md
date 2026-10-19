# Mini-Transformer Project Instructions

## Read before acting

Before modifying project files, read:
1. `docs/PRD.md`
2. `docs/TECH_SPEC.md`
3. `docs/AI_RULES.md`
4. `docs/DATASET_CARD.md`
5. `docs/AI_LOG_TEMPLATE.md`
6. `docs/ARCHITECTURE_DECISIONS.md`

These files are the source of truth. If there is a conflict, do not guess: report the conflict and ask the project coordinator to update the approved specification.

## Workflow

- Work on one GitHub Issue at a time and only modify files within its scope. Issues are mirrored locally in `issues/` (markdown); use them, no GitHub API/web access is needed.
- Before coding, state the planned approach, interfaces/tensor shapes, complexity, edge cases, and tests.
- Do not change public interfaces, architecture choices, dependencies, or unrelated files without approval.
- Prefer small changes that can be tested independently.
- Add or update tests for every behavior change.
- Do not claim a test passed unless you actually ran it and observed the output.
- The repository uses one branch only: `master`. Do not create new branches, pull requests, or merge operations. Commit and push directly to `master`. Run `git pull --ff-only origin master` only when a teammate notifies you they have pushed changes (work is sequential).
- Preserve meaningful AI interaction logs under `docs/ai-logs/`; never delete or fabricate logs.
- Never write secrets, API keys, access tokens, passwords, or personal sensitive data to logs or Git.

## Technical constraints

- Python + PyTorch.
- Build a small decoder-only Transformer for next-token prediction.
- Implement causal Multi-Head Self-Attention and sinusoidal positional encoding manually.
- Do not use `torch.nn.Transformer`, `torch.nn.TransformerDecoder`, or `torch.nn.MultiheadAttention` to replace the core attention/decoder implementation.
- It is permitted to use basic tensor operations, `nn.Linear`, `nn.Embedding`, autograd, `CrossEntropyLoss`, and optimizers.
- Do not use pretrained language-model weights or an external GPT API as the project model.
- Follow `docs/TECH_SPEC.md` for shapes and configuration.

## Response format for coding tasks

1. Restate the Issue scope briefly.
2. Explain implementation plan and algorithmic complexity where relevant.
3. Implement only the approved scope.
4. Run the applicable tests and report exact outcomes.
5. Summarize changed files, caveats, and the next required action.

## Do not do these things

- Do not invent acceptance criteria or dataset properties.
- Do not silently expand scope.
- Do not replace a manual implementation with a library abstraction that defeats the assignment.
- Do not edit approved specification documents as a side effect of implementing a feature.
