# Repository Agent Rules

## Tooling
- Use `uv` for dependency management and running commands.
- When adding dependencies, pin exact versions.
- Install the development environment with `uv sync --dev`.
- The repository uses a `src/` layout and tests must import the installed package.
- Do not modify `sys.path` in tests or add pytest/pythonpath import hacks.
- Run tests with `uv run pytest`.

## Code style
- Use modern Python 3.13+ style.
- Treat Python 3.13 as the baseline, not as an upper bound.
- Prefer current best practices and language features available in Python 3.13+ over older compatibility patterns.
- Do not introduce backward-compatibility constructs unless the repository explicitly needs them.
- Avoid legacy idioms when a clearer modern Python alternative exists.
- Prefer explicit code over clever abstractions.
- Use single quotes in Python code for regular strings. For any triple strings prefer double quotes.
- Use Google-style docstrings.
- If a function intentionally raises exceptions as part of its contract, document them in a `Raises:` section.
- Only document exceptions that callers are expected to handle or that represent meaningful API behavior.
- Do not document incidental internal exceptions from underlying libraries unless they are part of the method's intended behavior.

## Operating Assumptions

- Audience: personal use first (repo owner), with at most a few trusted users.
- Primary optimization: developer time is the most limited resource.
- Decision rule: prefer simpler code and explicit assumptions over defensive completeness.
- Reliability model: fail fast on unhandled exceptions so cloud restart/alerts surface issues immediately.
- Throughput expectations: low traffic and mostly sequential usage; high-scale patterns are out of scope.
- Buffering approach: soft/unbounded buffering can be acceptable when aligned with expected personal usage.
- Handler architecture: allow pragmatic orchestration in handlers; avoid splitting modules early without clear pain.
- Logging approach: keep logs human-readable and concise; cloud platform already provides timestamps/metadata.
- Correctness target: prioritize common-path behavior and maintainability over edge-case-heavy guard rails.
- Refactor trigger: add structure, guard rails, or stronger isolation only after concrete recurring pain.
- Pain signals include:
  - repeated production failures
  - difficult debugging with current logs/structure
  - growing user/message volume
  - handlers becoming slow or hard to modify safely
  - memory/runtime limits being reached

### Agent behavior under these assumptions

- Do not recommend heavy architecture changes by default for hypothetical scale.
- Treat some tradeoffs as intentional features, not defects, when they reduce maintenance cost.
- If suggesting stricter patterns, tie them to observed issues or explicit scale/operational changes.
- Prefer incremental improvements that preserve current simplicity and runtime behavior.
- End chat responses with short, practical next-step suggestions when natural follow-up actions exist.
- Keep next-step suggestions concise and optional (do not force extra work when none is needed).

### Recommendation policy

- Default to the smallest change that solves today's problem.
- Do not propose scale-oriented architecture without observed concrete pain.
- Mark recommendations as:
  - now: should be done immediately due to active impact
  - later: optional until a trigger/pain signal appears

### Accepted risks

- Some edge cases may remain intentionally unhandled to keep implementation small.
- Bounded resources and stricter isolation are added after incidents, not preemptively.
- Simplicity and maintenance speed are preferred over exhaustive defensive coding.

### Testing expectations

- Cover critical paths and regressions that already happened.
- Do not require exhaustive edge-case tests by default.
- Prefer fast unit tests; add integration tests only for high-risk or failure-prone flows.

## Code Review Expectations

When reviewing code in this repository, do not limit feedback to bug detection.

Also evaluate the following dimensions:

### Architecture

- Check whether abstraction boundaries match the intended layer.
- Infrastructure code should remain generic and independent from domain logic.
- Avoid introducing unnecessary layers, indirection, or premature abstractions.
- Prefer small, explicit modules over framework-like structures.

### Modern Python practices

- Prefer modern Python 3.13 idioms and language features.
- Avoid legacy compatibility constructs or patterns meant for older Python versions.
- Prefer explicit control flow and readable constructs over clever patterns.

### API design

- Public APIs should be minimal and stable.
- Helper methods should remain private unless there is a clear external use case.
- Method naming should reflect the abstraction level (infra vs domain).
- Avoid expanding the public surface area without clear benefit.

### Maintainability

- Prefer straightforward implementations that are easy to modify.
- Avoid unnecessary complexity, genericity, or configuration.
- Code should remain understandable by the repository owner after long gaps.

### Reliability

- Consider failure modes and resource lifecycle.
- Ensure cleanup paths exist where relevant (files, streams, clients).
- Fail-fast behavior is preferred over silent error masking.

### Naming

- Names should reflect the abstraction level and responsibility.
- Low-level infrastructure code should avoid domain semantics.

### Simplicity rule

If no functional bugs are found, still check whether:

- the implementation is the simplest clear solution
- unnecessary abstractions were introduced
- the public API can be smaller or clearer

Feedback should be grouped as:

- critical issues
- important improvements
- optional polish

Absence of bugs does **not** mean the review is complete. Design quality, clarity, and maintainability should still be evaluated.

## Commit Messages

Use Conventional Commits.

### Commit scope discipline

- Keep commits conceptually coherent by subsystem and intent.
- Do not ask to combine unrelated changes when scopes are clearly different
  (for example: `AGENTS.md` policy updates vs `src/` runtime code edits).
- When unrelated local modifications exist, commit only files relevant to the requested change by default.

Format:

type(scope): short description

Rules:
- types: feat, fix, refactor, chore, docs, test
- lowercase subject, imperative mood
- subject ≤ 72 chars
- add a body when reasoning matters
- body uses normal sentence capitalization

### Subject guidelines

The subject should describe the **system-level change**, not the exact
implementation detail.

Prefer short semantic descriptions of the capability or behavior added or
changed.

Examples:

- docs: add AGENTS.md with repository workflow guidelines
- docs: document commit scope rules
- feat(infra): add fail-fast detached task supervision
- refactor(services): simplify task scheduling logic

Implementation details such as **class names, modules, or files** should
normally appear in the commit body.

Example:

feat(infra): add fail-fast detached task supervision

Introduce `TaskSupervisor` for detached asyncio tasks with centralized
exception handling and a one-shot failure hook.

### Avoid vague subjects

Avoid overly abstract subjects such as:

- "add workflow instructions"
- "update agent rules"
- "improve system behavior"

Subjects should clearly indicate **what capability changed**.

### Scope

The scope should represent a **stable semantic subsystem of the repository**.

A scope is appropriate when a change clearly belongs to a long-lived
component or conceptual area of the system.

Scopes may match module or directory names **when those names represent
real architectural boundaries**.

Examples of valid subsystem scopes in this repository:

- `app` — application bootstrap and runtime wiring
- `handlers` — Telegram handlers and routing logic
- `services` — application services and domain utilities
- `infra` — shared infrastructure utilities (logging, async helpers, supervisors)
- `settings` — configuration loading, validation, and environment settings
- `deps` — dependency changes

Avoid inventing ad-hoc scopes based only on:

- a single touched file
- a temporary implementation detail
- an arbitrary directory that does not represent a subsystem

Prefer **precise established subsystem names** over broad buckets when both are valid.

### Root-level files

Changes to repository-level files (for example `README.md`, `AGENTS.md`,
`.gitignore`, `pyproject.toml`) should usually **omit scope**, unless the
change clearly belongs to a defined subsystem such as `deps`.

Examples:

docs: update README with setup instructions  
chore: update .gitignore  
chore(deps): pin development dependencies

### Generic infrastructure

If a change introduces a **generic reusable module** not tied to a specific
subsystem (e.g. async utilities, supervision helpers, logging
infrastructure), prefer the `infra` scope.

Example:

feat(infra): add fail-fast task supervisor for detached asyncio tasks

### Avoid incorrect scopes

Do **not** choose scope based only on:

- the directory where the file was added
- where the module is currently imported

For example, a generic async utility should **not** use:

- `app`
- `services`
- `handlers`

even if it is currently used there.

### When scope is unclear

If a change does not clearly belong to a stable subsystem, omit the scope.

Examples:

feat: add task supervisor utility  
chore: update development workflow instructions
