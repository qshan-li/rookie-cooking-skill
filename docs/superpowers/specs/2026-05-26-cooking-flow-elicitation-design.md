# Rookie Cooking Flow Elicitation Design

Date: 2026-05-26
Status: Ready for execution planning

## Context

`rookie-cooking` already has a strong recipe schema, a local memory CLI,
and prompt-level workflow rules for recipe generation, troubleshooting, meal
planning, recipe import, learning, and durable preference updates. The current
gap is product flow consistency.

Recipe Generation has the clearest interaction model: output-mode selection,
first-run adaptation, memory read, default fallback, and post-generation
delivery. Meal Planning has shopping-list elicitation. Troubleshooting reads
memory and creates pending candidates. Recipe Import, Learning, and Memory
Init / Update are defined as capabilities, but their user decision points are
not yet as explicit or testable as Recipe Generation.

This spec defines one shared elicitation contract and applies it to all six
major flows:

- Recipe Generation
- Troubleshooting
- Memory Init / Update
- Recipe Import
- Meal Planning
- Learning

The goal is not to make the agent ask more questions. The goal is to ask only
when the answer changes the output, always provide a low-friction default, and
turn every flow into a complete, reviewable unit.

This spec chooses the "flow contract plus test matrix" approach. The first
implementation should remain mostly prompt, reference, template, and QA harness
work. It should not introduce a standalone flow engine unless the documented
contracts prove impossible to test with stable prompt rules.

## Goals

- Make elicitation behavior consistent across all major flows.
- Preserve the existing rule that useful work should continue when optional
  interaction tools are unavailable.
- Reduce repeated open-ended questions by using small choice sets and compact
  forms.
- Make memory use visible, reversible, and explicitly confirmed before durable
  writes.
- Add clear post-flow actions so users can continue naturally: print, save,
  confirm memory, reject memory, adapt again, or end.
- Keep Recipe Generation's current default behavior: if the user only names a
  dish and no interactive choice tool exists, generate the full explanation
  version using defaults.
- Make Recipe Import, Meal Planning, Learning, and Troubleshooting as testable
  as Recipe Generation.

## Non-Goals

- No real-time cooking assistant mode.
- No built-in timers, notifications, or mobile app UI.
- No cloud sync or cross-device account system.
- No vector database or semantic memory retrieval.
- No automatic durable learning from conversation history.
- No host-specific hidden memory writes.
- No expansion of maintained recipe content in this spec.
- No generated PDFs or printer behavior changes beyond the existing delivery
  contract.

## Product Principles

Elicitation should be sparse and consequential:

- Ask only when the user's choice changes recipe parameters, output shape,
  safety handling, persistence, or delivery.
- Every elicitation must have a default option that allows progress.
- Prefer 2-4 options. More than 4 options should become a compact form or a
  later refinement step.
- If a flow can produce a safe useful answer with defaults, it must not block on
  optional information.
- Safety-critical unknowns are allowed to block. Examples: unknown doneness for
  poultry, suspected spoiled seafood, allergy exposure, unsafe leftovers.
- Durable memory writes require explicit confirmation.
- Sensitive durable memory requires a separate confirmation.
- Pending or low-confidence memory may influence ranking, but must be labeled
  as a suggestion.

## Elicitation Types

Every possible question should be classified before it is asked:

| Type | When to use | User experience | Fallback when no interaction tool exists |
| --- | --- | --- | --- |
| Blocking | Missing answer can make the output unsafe, invalid, or impossible to scope | Ask one short question and wait | Ask one short plain-text question and wait |
| Optional | Answer would improve fit, but defaults produce a useful result | Use choice chips or compact form with a default | Continue with defaults and state the assumption |
| Post-answer expansion | User may want more output after the core answer is delivered | Offer next actions after the answer | Ask a short follow-up or end cleanly |

Most cooking preference questions are optional. Most delivery, memory write,
and shopping-list-detail questions are post-answer expansion. Food safety and
durable persistence are the main places where blocking questions are justified.

## Shared Elicitation Contract

Every flow should follow this decision contract:

1. Classify the flow from the user's request.
2. Read relevant memory when the flow can benefit from it and the local script
   is available.
3. Decide whether a question is required, optional, or unnecessary.
4. Use an interactive choice tool when the runtime provides one.
5. If no interactive choice tool exists:
   - Continue with defaults when the question is optional.
   - Ask one short plain-text question only when the answer is required for
     safety or required to define the requested output.
6. Produce the requested artifact or answer.
7. State the preferences, assumptions, and memory suggestions used.
8. Offer only the next actions that are relevant to the completed flow.

The shared choice wording should stay stable enough for cross-agent tests:

- Continue with defaults
- Adapt this request only
- Initialize long-term preferences
- Save as draft
- Generate PDF
- Direct print
- No delivery
- Record feedback only
- Save durable preference
- Do not record
- View / change / delete memory
- Ignore memory once

## Flow Matrix

This table is the execution contract. Implementation plans should preserve the
matrix even if wording in the prose sections changes.

| Flow | Blocking questions | Default fallback | Memory read | Memory write | Post-answer actions | Minimum test oracle |
| --- | --- | --- | --- | --- | --- | --- |
| Recipe Generation | Safety-critical missing constraints only | Full explanation version, skill defaults | Dish, diners, equipment, taste, feedback | Only after explicit durable preference or confirmed candidate | PDF, direct print, no delivery; memory controls if used | Missing output mode does not block when tools are unavailable |
| Troubleshooting | Unsafe meat, poultry, seafood, eggs, leftovers, spoilage, allergy, or unknown doneness | Diagnose from observed facts and assumptions | Dish and diners when identifiable | Feedback candidate or durable preference only after confirmation | Record feedback only, save durable preference, do not record | Never triggers Recipe Generation QA; safety judgment appears before taste advice |
| Memory Init / Update | Confirmation before durable write; separate confirmation for sensitive data | Do not write; treat unclear values as session-only or candidate | Current profile and candidates | Through `scripts/cooking_memory.py` only | Confirm write, edit values, cancel, view/delete/ignore | Write preview appears before any durable write |
| Recipe Import | Persistence target and source note when saving a draft; high-risk safety gaps | Rewrite for this chat only, review status `draft` | Optional profile for equipment and taste adaptation | No durable user memory by default; recipe file only when user asks to save | Save draft, revise, review checklist, generate PDF, discard | Import preserves `draft` and does not mark content `passed` |
| Meal Planning | Required only when servings or menu scope is impossible to infer | Infer menu source; use relative timeline; skip full shopping list until selected | Servings, diners, equipment, taste, dislikes | No durable write by default | Replace dish, shopping list, kitchen bundle, PDF, end | Full shopping list appears only after explicit mode |
| Learning | Only when user asks to diagnose a specific unsafe failure without enough facts | Short explanation plus one practical link | Equipment and taste only when it changes explanation | No durable write by default | Full principle card, explain through dish, diagnose failed result | Default Learning does not block and does not trigger Recipe Generation QA |

## Flow 1: Recipe Generation

### Trigger

The user asks how to cook a dish, names a dish, asks for a recipe, or asks to
adapt a recipe to servings, equipment, taste, or a household member.

### Current Strength

Recipe Generation already has the most mature flow:

- output-mode elicitation when missing
- first-run adaptation when no profile exists
- default fallback when interaction tools are unavailable
- memory read before generation
- post-generation delivery choice
- temporary kitchen artifact for PDF or printing

### Optimization

Merge the first two Recipe Generation choices into a single start card when the
runtime supports richer structured input:

- Output mode:
  - Full explanation version, default
  - Kitchen execution version
- Adaptation:
  - Continue with defaults, default
  - Adapt this recipe only
  - Initialize long-term preferences

If the runtime only supports simple option chips, keep the existing sequential
flow: first output mode, then first-run adaptation.

### One-Time Adaptation Form

When the user chooses "Adapt this recipe only", ask a compact form:

- servings
- stove type
- pan type
- scale available
- thermometer available
- salt level
- oil level
- spice level
- dislikes or temporary constraints

All fields are optional except servings when the user has already implied a
group size but not given a number. These answers are session-only and must not
write to memory.

### Output

The generated recipe must include:

- dish metadata
- ingredients with grams or milliliters and no-scale fallback
- step timing, heat level, target state, failure signal, and reason
- safety notes
- substitutions
- failure diagnosis
- related principles
- applied preferences or assumptions

### Post-Flow Actions

After generation, offer delivery choices:

- Generate PDF
- Direct print
- No delivery

If memory feedback was used, also make memory controls visible:

- View / change / delete memory
- Ignore memory once

Do not mix memory controls into the delivery choice if that would create more
than 4 choices. Put memory controls in a short "Memory used" note after the
delivery choice.

## Flow 2: Troubleshooting

### Trigger

The user reports a failed or unexpected result: texture, flavor, doneness,
water release, burning, separation, odor, leftovers, reheating, or food-safety
concern.

### Required Safety Triage

Before texture or taste advice, classify safety risk:

- meat, poultry, seafood, eggs, leftovers, thawing, or reheating involved
- suspected spoilage, off smell, sliminess, mold, or unsafe storage
- undercooked high-risk ingredient
- allergy or sensitive diner concern

If the safety risk is high and the required fact is missing, ask one blocking
question. Example: "这道菜含鸡肉吗，且中心是否还有粉色或流出生肉汁？"

If the risk is not high or enough facts exist, continue directly.

### Issue Taxonomy

Troubleshooting should normalize common failure descriptions into stable issue
labels before proposing memory writes. The first implementation should support
at least:

| Issue label | User-facing symptoms | Typical next-run parameters |
| --- | --- | --- |
| `too_salty` | 太咸、咸到发苦、收汁后过咸 | salt multiplier, soy sauce amount, dilution, sauce reduction |
| `too_bland` | 太淡、不入味、没鲜味 | salt timing, seasoning amount, marinade time |
| `too_watery` | 出水、汤太多、口感闷 | batch size, draining, salt timing, heat level |
| `burnt` | 糊底、发黑、苦味、糖糊 | heat level, oil amount, stirring interval, sugar timing |
| `undercooked` | 没熟、夹生、中心发粉或透明 | cook time, cut size, covered heating, safety endpoint |
| `meat_dry` | 肉柴、老、硬 | cook time, cut thickness, velveting, resting |
| `separated` | 乳化失败、油水分离、蛋羹蜂窝 | heat level, water ratio, mixing, steaming intensity |

The label is not shown as a diagnosis by itself. It is used to keep feedback
records and candidate memory stable across agents.

### Diagnostic Output

Troubleshooting must separate:

- observed facts
- safety judgment
- assumptions
- likely causes, ranked
- immediate salvage steps when safe
- next-run parameter changes
- memory used
- memory write proposal

### Memory Use

If the dish is identifiable, read memory with:

```bash
python scripts/cooking_memory.py read --dish <recipe-id> --diners <member-id...>
```

Memory can rank likely causes, but cannot silently become fact. Pending
feedback remains a suggestion.

### Post-Diagnosis Memory Choice

After giving the diagnosis, offer a memory action when the user's feedback is
useful:

- Record feedback only: write pending feedback or candidate; do not change
  durable preferences.
- Save durable preference: only when the user explicitly confirms a durable
  rule such as "以后这道菜少盐".
- Do not record: end without memory write.

If no interactive choice tool exists, ask a short non-blocking question after
the diagnosis. Do not delay salvage or safety advice.

## Flow 3: Memory Init / Update

### Trigger

Enter this flow only when the user explicitly asks to initialize, update, view,
delete, ignore, or confirm durable cooking preferences or memory candidates.

Do not enter it merely because no profile exists.

### Init Wizard

The initial wizard should prioritize fields that change recipe output:

- default servings
- stove type
- pan type
- has kitchen scale
- has thermometer
- salt level
- oil level
- spice level
- common dislikes

Household members are optional second-stage fields:

- member id or display name
- taste preferences
- dislikes
- sensitive constraints

Sensitive constraints must be confirmed separately before durable write:

- allergies
- pregnancy
- child-specific food rules
- diseases or medical constraints
- religion or long-term dietary restrictions

### Update Flow

For updates, classify the user's wording:

- Current request only: do not write memory.
- Durable global preference: write to profile after confirmation.
- Dish-specific durable preference: write to `recipe_preferences` after
  confirmation.
- Unclear preference: create or propose a memory candidate.

### Write Preview

Before any durable write, show a compact preview:

```text
Will write:
- defaults.servings = 4
- equipment.stove_type = induction

Will not write:
- tonight_no_cilantro, session-only
```

Then ask for explicit confirmation. If the runtime has an interactive choice
tool, choices are:

- Confirm write
- Edit values
- Cancel

The current CLI can perform writes but does not yet expose a dedicated
`--dry-run` mode. The first implementation may generate the preview in prompt
space from parsed user intent. If tests show this is too fragile, add a small
CLI dry-run command before broadening the memory wizard.

### Memory Management Actions

Memory management should expose:

- view current profile
- list pending candidates
- confirm candidate
- reject candidate
- delete profile path or candidate
- ignore dish memory once

All durable operations must go through `scripts/cooking_memory.py`.

## Flow 4: Recipe Import

### Trigger

The user provides an external, pasted, screenshot-summarized, or self-authored
recipe and asks to rewrite, organize, review, save, or make it beginner-friendly.

### Import Intent Choice

Import has two separate decisions: persistence target and output shape. Do not
merge them into one choice set.

When the persistence target is missing and an interactive choice tool is
available, ask:

- Rewrite for this chat only, default
- Save as draft recipe
- Review an existing draft

If no interaction tool exists, default to rewriting for this chat only and keep
the review status as `draft`.

Output shape follows the existing recipe output rules:

- Full explanation version, default
- Kitchen execution version
- PDF or direct print only after a kitchen execution version exists

If the user asks to save as a draft and also asks for kitchen execution, do
both: save the draft boundary and produce the requested output shape.

### Required Source Handling

The import flow must capture or state:

- source description
- original dish name
- original servings if available
- main ingredients
- key steps
- ambiguous terms and missing parameters
- copyright-safe rewrite boundary
- review status: `draft`

If the user asks to save into the maintained recipe library, require a source
note and draft status. Do not mark imported content as `passed` or `validated`
without the existing review and kitchen validation processes.

### Missing Parameter Elicitation

Do not ask about every missing detail. Fill routine gaps with documented
defaults and label them as defaults or ranges.

Ask only when one of these is missing and cannot be safely inferred:

- high-risk ingredient safety handling
- target serving count for a saved recipe
- whether the user wants the result persisted
- source description for a persisted draft

### Output

The import output should include:

- rewritten full explanation version or requested kitchen execution version
- import review record using `templates/imported-recipe-review.md`
- list of changed ambiguous terms
- open risks
- next action: keep draft, revise, review checklist, generate PDF, or discard

## Flow 5: Meal Planning

### Trigger

The user asks for a meal, multiple dishes, menu, cooking schedule, shopping
list, equipment coordination, or "two dishes and one soup" style planning.

### Planning Mode Inference

Meal Planning should infer the planning mode before asking. Ask only when the
mode cannot be inferred from the request and the plan would materially differ.

Inference rules:

- named dishes present: use those dishes
- ingredients present without dishes: plan from available ingredients
- no dishes or ingredients, but a meal shape exists: recommend from existing
  recipes
- explicit shopping request: include shopping-list elicitation

When the menu source is still ambiguous and an interactive choice tool is
available, ask:

- Use dishes I name, default when user already named dishes
- Recommend from existing recipes
- Plan from ingredients I already have

If no interaction tool exists and the mode remains ambiguous, recommend from
existing recipes using defaults and state that assumption.

### Required Inputs

Ask only when the missing answer changes the plan materially:

- servings or diners
- mealtime deadline
- available equipment
- whether shopping list is needed

If no mealtime is supplied, output a relative timeline such as `T-90`.

### Shopping List Elicitation

Keep the existing shopping-list choice, but make it a reusable step:

- Full shopping list
- Missing-items checklist
- Skip shopping list

The menu, equipment conflicts, and kitchen schedule may be produced first. Full
shopping-list details must wait for this choice unless the user explicitly
requested them.

### Output

The plan must include:

- menu
- servings and diners
- equipment summary
- kitchen timeline
- equipment conflicts
- high-risk non-parallel actions
- long-wait checkpoints or alarm suggestions
- shopping list according to selected mode
- applied preferences and assumptions

### Post-Flow Actions

Offer follow-up actions that fit the produced meal plan:

- Replace a dish
- Generate shopping list
- Generate kitchen execution bundle
- Generate PDF
- End

Do not offer all actions if the flow already included the relevant artifact.

## Flow 6: Learning

### Trigger

The user asks why something works, why something failed, what a cooking term
means, or how to understand a technique.

### Learning Depth And Expansion

Learning should not start with a question unless the user explicitly asks for a
specific output shape and that shape is ambiguous. The default is a concise
answer.

After the concise answer, offer post-answer expansion choices when the runtime
supports them:

- Full principle card
- Explain through one dish
- Diagnose my failed result

If no interaction tool exists, end with a short note that the user can ask for
the full principle card, a dish example, or diagnosis. Do not block.

### Memory Use

Learning should read relevant memory when it changes the explanation. Examples:

- no thermometer: explain oil temperature through chopstick bubbles, sound,
  shimmer, and smoke point instead of only Celsius values
- induction cooktop: explain heat response and pan contact
- low spice preference: choose non-spicy example dishes
- repeated failure for a dish: connect the principle to that failure as a
  suggestion

### Output

Short answer output:

- one-sentence explanation
- key variables
- beginner check
- one concrete application
- one linked recipe or practice dish

Full principle card output:

- use `templates/principle-card.md`
- include principle explanation, key variables, applications,
  counterintuitive cases, mistakes, source note, and linked recipes

If the user chooses "Diagnose my failed result", transition to
Troubleshooting. Do not run Recipe Generation output selection.

## Data And State

The design reuses existing local memory files:

```text
~/.rookie-cooking/
  profile.yaml
  feedback.jsonl
  memory-candidates.jsonl
```

No new persistence file is required for the first implementation. The existing
memory CLI remains the single write path:

```bash
python scripts/cooking_memory.py read --dish <dish> --diners <diners...>
python scripts/cooking_memory.py init-profile
python scripts/cooking_memory.py update-profile --set <path=value>
python scripts/cooking_memory.py add-feedback --recipe <recipe> --issue <issue>
python scripts/cooking_memory.py list-candidates
python scripts/cooking_memory.py confirm-candidate <candidate_id>
python scripts/cooking_memory.py reject-candidate <candidate_id>
python scripts/cooking_memory.py delete <path-or-id>
python scripts/cooking_memory.py ignore-once --dish <dish>
```

This spec may require extending script issue vocabularies or adding friendlier
CLI output later, but it does not require a new storage model.

Expected CLI gaps to evaluate during implementation:

- whether `add-feedback` needs the issue taxonomy above as explicit accepted
  values
- whether a dry-run or preview command is needed for memory writes
- whether `read` output should expose a smaller user-facing summary for
  "memory used" sections

## Error Handling

Missing memory is not an error. Continue with skill defaults.

Invalid memory should produce a clear notice and fall back to defaults for the
current response. Do not block recipe generation, meal planning, learning,
recipe import, or troubleshooting unless the missing fact is safety-critical.

Interactive choice tools may be unavailable. In that case:

- optional choices become default assumptions
- safety-critical choices become one short plain-text question
- delivery choices may be asked in plain text after the artifact is produced

Printer or PDF failures should use the existing delivery fallback:

- Generate PDF
- Output kitchen execution text

## Documentation Changes

Implementation should update:

- `SKILL.md`: add the shared elicitation contract and flow-specific choices.
- `references/cooking-memory-layer.md`: document memory init/update wizard,
  write preview, possible dry-run gap, and post-diagnosis memory choice.
- `references/recipe-import-rules.md`: document import intent choice and
  missing-parameter elicitation, separating persistence target from output
  shape.
- `references/meal-planning-rules.md`: document planning mode choice and
  post-flow actions, with inference before asking.
- `templates/failure-diagnosis.md`: ensure safety triage and memory action are
  explicit.
- `templates/imported-recipe-review.md`: include import intent and open risks.
- `templates/principle-card.md`: support short-answer and full-card mapping
  where needed.
- `README.md`: update user-facing examples for all six flows.
- `docs/interactive-qa-agent-test-plan.md`: extend the QA matrix beyond Recipe
  Generation.

## Tests

Add or update focused tests for prompt/document behavior:

- Recipe Generation still offers only full explanation and kitchen execution
  output modes.
- First-run adaptation still defaults to continuing with defaults.
- Troubleshooting never triggers Recipe Generation output-mode QA.
- Troubleshooting includes safety triage and post-diagnosis memory action.
- Memory Init / Update requires explicit durable write confirmation.
- Sensitive memory writes require separate confirmation.
- Recipe Import offers or defaults import intent and preserves `draft` status.
- Recipe Import does not mix persistence target with output shape.
- Meal Planning infers planning mode when possible and asks shopping-list mode
  before full list details.
- Learning defaults to a short answer without blocking, then offers expansion.
- Learning supports full principle card, dish explanation, and troubleshooting
  transition.
- Unsupported interactive tools fall back without blocking optional flows.
- Cross-agent QA checks cover Recipe Generation, Troubleshooting, Learning,
  Meal Planning, Recipe Import, and Memory Init / Update.

Existing repository checks should continue to pass:

```bash
python -m unittest discover -s tests
python scripts/check_skill_completeness.py
```

## Implementation Scope

This should be one implementation plan, but split internally by flow:

1. Add shared elicitation contract wording to `SKILL.md`.
2. Tighten Recipe Generation wording without changing its default behavior.
3. Add Troubleshooting safety triage and memory action.
4. Add Troubleshooting issue taxonomy for stable feedback candidates.
5. Add Memory Init / Update wizard and write preview.
6. Decide whether the memory CLI needs dry-run support.
7. Add Recipe Import intent choice and persistence boundary.
8. Add Meal Planning planning mode inference and post-flow actions.
9. Add Learning default-short-answer behavior and troubleshooting transition.
10. Update templates, references, README, and QA docs.
11. Add tests that enforce the new flow contracts.
12. Run unit tests and completeness checks.

The first implementation should not change maintained recipe files. It should
only change skill instructions, references, templates, docs, tests, and small
memory CLI behavior if the tests prove a script gap.

## Acceptance Criteria

- A user can enter any of the six flows without being routed through the wrong
  Recipe Generation QA.
- Optional elicitation never blocks useful output when interaction tools are
  unavailable.
- Safety-critical missing facts can still block with one short question.
- Every durable memory write has an explicit confirmation path.
- Recipe Import never persists or marks imported content as trusted without
  draft/review boundaries.
- Meal Planning never dumps a full shopping list before shopping-list mode is
  selected or explicitly requested.
- Learning stays concise by default, does not ask a first-turn depth question,
  and can transition to Troubleshooting when the user describes a failed result.
- Memory write previews are either generated reliably from parsed intent or
  backed by a CLI dry-run path before broad rollout.
- Cross-agent QA can detect the main regressions using stable wording.
