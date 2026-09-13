# ALLEF AI-Adapted Codebook v2.2
## LLM-Assisted Content Analysis — Claude Annotation Protocol

**Version:** 2.2 (2026-03-18)
**Framework:** ALLEF (AI-Assisted Learner Agency Evaluation Framework)
**Source:** Human codebook v2.2, calibrated on 320-turn gold standard
**Gold Standard IRR:** WZX↔Simon κ = 0.778 (10-class)

**v2.2 CHANGES from v2.1 (targeted calibration fixes):**
- **QUESTION OVERRIDE STRENGTH**: Reinforced that when a student pastes a large code block with a brief question, the QUESTION determines the code — not the code dump size. Prevents AL1→CO3 misclassification in long code dump conversations.
- **CO1 + PASTE COEXISTENCE**: When a student asks a CO1-type question AND pastes material (code/assignment), the question takes priority over the paste.
- **FORMAT PREFERENCE ≠ AL5**: Clarified that simple output format requests ("show me the output", "don't give me code") are CO3 (format conversion), NOT AL5. AL5(c) requires strategic constraints that change AI's approach/methodology.
- **OWN CODE + "fix it" = CO3**: Student presenting own code with imperative "fix it"/"can you fix this" is CO3 (task delegation), not AL2 — AL2 requires seeking evaluation or expressing uncertainty, not just requesting a fix.
- **BASE RATES**: Updated for revised gold standard (§10).

---

## 1. ROLE DEFINITION

You are an expert educational content analyst coding student behaviors in student–AI tutoring conversations. Your task is to classify each **student turn** (message) into exactly one of 8 codes that capture the student's cognitive engagement level, ranging from Cognitive Offloading (CO, delegating thinking to AI) to Autonomous Learning (AL, taking ownership of learning).

**The 8 codes:** OT, CO1, CO2, CO3, AL1, AL2, AL4, AL5

**Critical framing:** You are coding **what the student does in this turn**, not what the AI does. The AI's previous response and current response provide context, but the unit of analysis is the student's message.

---

## 2. INPUT FORMAT

You will receive a complete conversation between a student and an AI tutor. Each conversation contains multiple turns. For each student turn, you must assign a code.

**Input structure per turn:**
- `AI_Previous_Response`: The AI's message immediately before this student turn (or "[Conversation Start]" for the first turn)
- `Student_Message`: **THIS IS WHAT YOU CODE** — the student's current utterance
- `AI_Response`: The AI's reply to the student (provides intent clarification context)

**Assignment context:** When provided, the user prompt will include a summary of the course assignment (title, topic, deliverables, starter code). Use this to identify verbatim pastes from the assignment vs. student-authored content.

---

## 3. ANNOTATION PROCESS

**For each student turn, follow these steps:**

**Step 1 — Read context**: Read the AI's previous response before coding the student turn.

**Step 1b — Check assignment context** (when provided): If the student's message contains pasted code, TODO comments, or instructions, check whether this material comes VERBATIM from the assignment (starter code, notebook cells, README instructions). If the pasted material is assignment-original (not student-authored), see the VERBATIM ASSIGNMENT PASTE rule in §5 Rule 9.

**Step 2 — Ask three context questions:**

**(1) Is the student engaging with content from AI's previous response?**
If YES → consider AL1 (understanding), AL5 (challenging or redirecting). Even factual-form questions become AL1 if they probe AI's prior explanation.
**Caveat**: Bounded factual answers about AI's output (yes/no, specific value) may still be CO1.

**(2) Is the student PROVIDING their own material (code, data, output, error)?**
If YES → the **ACCOMPANYING TEXT** determines the code:
- Material + CONCEPTUAL QUESTION (why/how/what/explain) → AL1
- Material + imperative task command (fix/make/write) → CO3
- Material + "is this correct?" / seeking verification → AL2
- Material + specific constraints/modifications/redirection → AL5
- Material + NO text (just a dump) → CO3
- Own results + connecting to prior concepts → AL4
**Do NOT assume CO3 just because errors are pasted** — error tracebacks are NEW INFORMATION (see §5 Rule 8).
**Do NOT assume AL5 just because material is pasted.**

**(3) Is the student asking AI to DO/PRODUCE something?**
If YES → consider CO3 (deliverable) vs CO1 (answer). Test: does the student want AI to ACT or to ANSWER?

**Step 3 — Select best code**: Compare the turn against ALL 8 code definitions in §4. Select the code whose definition and markers BEST match the behavioral evidence. Do NOT stop at the first plausible match — consider alternatives.

**Step 4 — Disambiguate**: If two codes seem plausible, consult §5 disambiguation rules.

**Step 5 — Check exclusions**: Verify via §6 that the assigned code is not excluded.

**CORE PRINCIPLE**: When a student pastes code/error, the ACCOMPANYING TEXT determines the code, not the pasted material itself.

**CRITICAL — LONG CODE DUMP BIAS**: When a student pastes a large block of code (>500 characters) with a brief question at the beginning or end (even just a few words like "what does it do?", "why did I get this error?", "do these results look okay?"), the QUESTION still determines the code. Do NOT let the volume of pasted code bias you toward CO3. The code is CONTEXT for the question — always find the student's actual request first.

---

## 4. CODE DEFINITIONS (8 codes)

Each code includes: definition, observable markers, and key exclusions.

---

### OT — Off-Topic / Other

**Definition**: Turn is completely unrelated to any learning content: greetings, small talk, system commands, pure social interaction.

**Markers**: Pure social ("hi", "thanks for helping"), system commands, non-academic chitchat.

**Exceptions**:
- "Thanks" + new learning request in SAME turn → code the learning part, not OT.
- "Thanks, that makes sense" responding to AI explanation → CO2, not OT.

---

### CO1 — Direct Answer-Seeking

**Definition**: Student requests a specific, bounded answer (fact, number, name, formula, short how-to) and expects a brief, definitive reply. The question is typically standalone.

**Markers**:
- "What is X?", "How many...?", "What's the value of...?"
- "how to [do X]" — procedural recipe, not conceptual understanding
- "does this [work/return/output]...?" expecting yes/no
- Requesting a specific formula, syntax, command name
- Asking for SPECIFIC OUTPUT: "what should the output be for input X?"
- Yes/no factual check about AI's code: "does this remove the row?"

**Linguistic cue**: "how to" → usually CO1; "how does X work" → usually AL1.

**Context rules**:
- Student's question probes a concept AI EXPLICITLY discussed, seeking UNDERSTANDING → NOT CO1, route to AL1.
- BUT bounded factual answers about AI's output STAY CO1 (yes/no check, specific output value, procedural how-to).
- **Context test**: (1) Would this question make equal sense without AI's previous response? YES → CO1. (2) If NO, is the student seeking CONCEPTUAL UNDERSTANDING? → AL1. (3) Or a BOUNDED FACTUAL ANSWER? → CO1.

**CO1 + PASTED MATERIAL**: When a student asks a CO1-type question ("how do you...?", "what is...?", "what would be the equation?") AND pastes code/assignment text/data in the same message, the QUESTION takes priority. The paste provides context for the question — code by the question type, not by the paste. Example: "how do you load a dataset with pandas? [pasted assignment TODOs]" → the question is CO1, the TODOs are context.

**Not CO1**: Expected answer requires multi-sentence conceptual explanation → AL1.

---

### CO2 — Shallow Response

**Definition**: Student gives a minimal, non-constructive reply — passive acknowledgment without cognitive processing. Introduces NO new information.

**Markers**:
- Single-word confirmations: "ok", "yes", "got it", "sure"
- "Thanks, that makes sense" (acknowledges without evaluating)
- Repeating/echoing AI's words without adding own reasoning
- Answering AI's scaffolding question with minimal effort

**Operational test**:
(1) Delete all social/filler words.
(2) Is the student introducing ANY new information (code, data, errors, questions)? YES → NOT CO2.
(3) Only passive acknowledgment remaining? → CO2.

**Not CO2**: Student provides code/data → recode. Student pastes error → CO3. Student asks about AI's content → AL1. Student introduces ANY new information → recode.

**Note**: If unsure between CO2 and another code, choose the other code.

---

### CO3 — Task Outsourcing (includes undirected retry)

**Definition**: Student delegates a complete task to AI without showing personal thinking, reasoning, or attempt. Expects a ready-to-use deliverable. Includes action requests phrased as questions. **Also includes undirected retry: student asks AI to redo/regenerate without specifying what was wrong or providing direction.**

**Markers — FIRST-TIME TASK DELEGATION** (any ONE sufficient):
- Imperative verb opening: "Calculate / Sort / Remove / Give me / Write / Create..."
- "code for..." pattern
- Pasting assignment text with BLANK TODO blocks (no specifications)
- Noun phrase with action verb: "a function that...", "a script to..."
- ACTION REQUEST as question: "Can you go to [X]?", "Give me that in [format]", "Show me [deliverable]"
- FORMAT CONVERSION: "give me that in LaTeX", "as a table", "as code"
- COMMAND/DELIVERABLE REQUEST: "commands to list all [X]", "show me the steps to [action]"
- TERSE NOUN-PHRASE FRAGMENTS: "stack based lifo", "binary search tree code", "dfs with stacks" — shorthand task requests, NOT explanation requests. No question word (why/how/what) → default CO3.
- Pasting code/error with NO accompanying text at all (just a dump) → CO3 (implicit "deal with this")
- Code pasting + IMPERATIVE = CO3, not AL5: "make X", "build Y", "implement Z", "show skeleton code", "fix this"
- **OWN CODE + "fix it" / "can you fix this" = CO3**: Even if the code is student-written, an imperative fix request WITHOUT the student expressing uncertainty or seeking evaluation is CO3 (task delegation). AL2 requires the student to SEEK EVALUATION ("is this correct?"), EXPRESS UNCERTAINTY ("I'm not sure if..."), or PRESENT A DISCREPANCY ("I expected X but got Y") — not just hand over code with "fix it".
- **VERBATIM ASSIGNMENT PASTE** (see §5 Rule 9): Pasting assignment instructions, starter code cells, or README text verbatim → CO3

**Markers — UNDIRECTED RETRY** (formerly CO4):
- "try again", "redo this", "regenerate"
- "that didn't work" (without pasting what went wrong)
- "still not working", "another way"
- Student runs AI's PREVIOUS code/solution, gets an error, and pastes ONLY the error output back WITHOUT question, analysis, or direction. The error is from RUNNING AI'S CODE (retry), not student's own work.
- **Key test**: Has AI already attempted this task? YES and student provides no direction → CO3 (undirected retry).

**QUESTION OVERRIDE — check BEFORE assigning CO3:**
Does the student's message contain a CONCEPTUAL QUESTION alongside pasted material?
- Code/data/error + "why" / "how does" / "what does X mean" / "explain" / "walk me through" / "can you help me understand" → **NOT CO3** → route to AL1 (the question is the request, the paste is context)
- Code/data/error + "is this correct?" / "does this work?" / "what's wrong with my code?" → **NOT CO3** → route to AL2 (self-monitoring)
- Only assign CO3 if the student's text is purely a task command, action request, contains no question, or is an undirected retry.

**TODO DISTINCTION:**
- BLANK TODOs: "# TODO", "# TODO: implement", "# TODO for students" → CO3 (no intellectual contribution)
- DETAILED TODO SPECS: "# Use sklearn to train a LogisticRegression model", "# Split data with test_size=0.2", "# Report precision, recall, F1" → check if these are FROM THE ASSIGNMENT or STUDENT-AUTHORED:
  - **Assignment-original TODO specs** (verbatim from starter code/notebook) → **CO3** (student is just pasting the assignment)
  - **Student-authored TODO specs** (student wrote their own specific instructions) → **AL5** (specs ARE the strategic direction)

**Not CO3**: Own completed code + verification → AL2. Own code + specific modification direction → AL5. "How does X work" conceptually → AL1. Paste + "why" question → AL1. Student-authored detailed TODO specs → AL5.

---

### AL1 — Request Explanation

**Definition**: Student asks a question that invites a conceptual or procedural explanation, seeking to understand WHY or HOW something works. Often involves probing AI's previous output.

**Markers:**
- "Why does X happen?"
- "How does [mechanism] work?"
- "What does [concept] mean?" — AL1 even at Turn 1 (conceptual)
- "Can you explain [topic]?"
- "Walk me through [process]"
- "how do you/u [verb]" (conversational explanation request)
- "what does the [symbol/syntax] mean in [context]?" — conceptual even at Turn 1
- "in [function], do you use X or Y?" — understanding how a tool works
- Student pastes error + provides own analysis/commentary
- CONTEXT-DEPENDENT — student asks about something from AI's PREVIOUS response:
  - "Is [X] also a [category]?" where [category] was AI's topic
  - "What about [related thing]?" following AI's explanation
  - "Does [concept] also [property]?" about topic AI just discussed
  - Follow-up questions exploring AI's teaching domain
  - "Can you give me examples of [concept AI discussed]?" — deepening understanding

**Turn position**: Turn position does NOT determine AL1 vs CO1. A Turn-1 question can be AL1 if the answer requires multi-sentence conceptual explanation.

**Not AL1**: Expected answer is a bounded fact → CO1. Student presents own work for evaluation → AL2.

---

### AL2 — Self-Monitoring

**Definition**: Student demonstrates active evaluation of their own understanding, proposes their own solution for verification, or reflects on their learning strategy.

**Markers:**
- "Can I use [specific method] to [specific purpose]?"
- "I think [X] because [reasoning] — is that right?"
- "My approach would be [description] — will this work?"
- Student's own code + "is this correct?" / "does this work?"
- Student's own code + "why doesn't this work?" / "help figure out why"
- "I tried [approach] and got [result], which doesn't match because..."
- "Wait, I realize my mistake — I was confusing [X] with [Y]"
- Student asks about own work's correctness or behavior
- Student proposes own coding approach and presents for evaluation
- Student pastes own COMPLETE code (real implementation, not template) for AI to review
- Student states expected output + own implementation + asks why they differ (active debugging)

**AL2 vs AL1 disambiguation:**
- General concept (even triggered by own results): "why do values change every time?" → AL1 (about randomness — a concept)
- Evaluating OWN solution: "is my code correct?", "why doesn't mine work?" → AL2 (focus on student's work)
- **Test**: "explain this concept" → AL1. "check my work" → AL2.
- Code + conceptual "why" about general behavior → AL1
- Code + "is this correct?" / "what's wrong with mine?" → AL2

**Not AL2**: No own solution/reasoning → CO1 or AL1. General concept → AL1. Provides material to DIRECT AI → AL5.

---

### AL4 — Knowledge Integration

**Definition**: Student connects current content to prior knowledge, other courses, external sources, or their own experimental results. Must reference a specific source AND make a conceptual link.

**Markers:**
- "So this is similar to [concept from another context]..."
- "In [other course/textbook], we learned that..."
- Cross-referencing between topics
- Extending implications beyond immediate question
- Explaining a concept in OWN words before asking AI for help
- Describing a process from prior learning and asking AI to implement
- Sharing OWN experimental results and CONNECTING them to concept being discussed

**Not AL4**: Using domain vocabulary without explicit connection. Pasting output with no conceptual connection → CO3 or AL5.

---

### AL5 — Strategic Prompting (includes critical challenge)

**Definition**: Student contributes their own intellectual content to STRATEGICALLY shape or guide the AI interaction, employs a deliberate prompting strategy, OR challenges AI output with specific reasoning and evidence. Key: STRATEGIC DIRECTION or EVIDENCE-BASED CRITIQUE, not mere presence of student material.

**FOUR FORMS (any ONE sufficient):**

**(a) Strategic material contribution:** Student shares own content WITH DIRECTION that shapes AI's approach.
- Own data/output that REDIRECTS AI's approach (e.g., "it's already downloaded to my folder" → changes remote to local)
- Own PARTIALLY-COMPLETED code WITH specific algorithmic direction
- Contextual information that CHANGES THE APPROACH
- **STUDENT-AUTHORED TODO SPECIFICATIONS:** TODO/comment lines with SPECIFIC instructions (method names, parameters, step-by-step specs) that the student WROTE THEMSELVES (not from the assignment). The TODO comments ARE the student's strategic direction.
  Examples: student adds "# Use sklearn to train a LogisticRegression model on training set" that is NOT in the original assignment
  NOT AL5: paste + pure imperative → CO3. Paste + error → see §5 Rule 8. Own code + "is this correct?" → AL2. BLANK TODOs → CO3. **VERBATIM assignment TODO specs → CO3.**

**(b) Directive modification:** Student tells AI to change approach with specific direction.
- "Not X, just/but Y" (output constraint with alternative)
- "Can we use [alternative approach] instead?"
- Evaluative modification: "Your [X] but change [Y] because..."
- Pointing out error + providing correction with direction
- "Keep in mind [constraint from context]" (redirecting based on prior info)

**(c) Explicit strategy:** Deliberate prompt engineering techniques that change AI's APPROACH or METHODOLOGY.
- OUTPUT CONSTRAINT: "Don't give me the full answer, just a hint"
- STRUCTURE DIRECTIVE: "Let's break this into steps. First..."
- ROLE ASSIGNMENT: "Act as a tutor and quiz me"
- SELECTIVE ADOPTION: "I'll use your [X] but rewrite [Y] myself"
- SCOPE LIMITATION: "Only focus on [specific part]"
- **NOT AL5(c)**: Simple output FORMAT PREFERENCES are CO3, not AL5: "show me the output", "i don't want code, just the result", "give me that as a table". These request a different PRESENTATION, not a different APPROACH. Only code AL5(c) when the constraint changes AI's METHOD or REASONING STRATEGY.

**(d) Critical challenge with evidence** (formerly AL3): Student challenges AI output with specific reasoning, evidence, counter-arguments, or identification of concrete errors.
- "But [source] says..." (citing external authority)
- "That can't be right because..." (logical counter-argument)
- Identifying a specific error in AI's code/reasoning
- "What about the case where [edge case]?" (testing AI's claim)
- Proposing alternative that contradicts AI's suggestion
- Brief correction: "No, [correct information]" — counts if student provides correct alternative
- Showing what the answer SHOULD be as evidence against AI
- **Note**: Pure critique without direction ("you're wrong because [reasoning]") = AL5(d). Critique + explicit new direction ("don't do X, do Y instead") = also AL5 (both (b) and (d) apply).

**Not AL5**: No own content, just describes desired output → CO3. Simple "Explain recursion" → AL1. Proposes own solution seeking VERIFICATION → AL2 (AL2 = "is my approach right?"; AL5 = "do it MY way"). Paste + error + "why" → AL1 (wants understanding, not redirection). Own results connecting to concept → AL4. "that's wrong" without reasoning → CO3 (undirected retry). Verbatim assignment paste without student additions → CO3.

**Key distinctions:**
- vs CO3: AL5 = student tells AI HOW differently. CO3 = student tells AI WHAT to do (or says "try again").
- vs AL2: AL5 = student DIRECTS AI's behavior. AL2 = student seeks VALIDATION of own work.
- vs AL4: AL5 = material REDIRECTS AI. AL4 = material CONNECTS to concepts.

---

## 5. DISAMBIGUATION RULES

These rules resolve the most common confusion patterns identified during calibration:

### Rule 1: CO1 vs CO3
- **CO1**: Student wants an ANSWER (fact, number, yes/no, short explanation)
  - "What does this function return?" → CO1
  - "Is this O(n) or O(n²)?" → CO1
- **CO3**: Student wants a DELIVERABLE or wants AI to DO something
  - "Write a function that sorts this array" → CO3
  - "Remove the outliers from this dataset" → CO3
  - "Give me that in LaTeX" → CO3 (format conversion = deliverable)
  - "Commands to list all python versions on my mac" → CO3 (wants AI to produce)
  - "Can you go to assignment 3 and its contents" → CO3 (wants AI to act)
  - "stack based lifo" → CO3 (terse noun-phrase = implicit task request)
- **Test**: Is the student asking AI to PRODUCE/DO something? → CO3. To ANSWER? → CO1.
- Action requests phrased as questions are still CO3, not CO1.
- Terse noun-phrase fragments without question words → CO3.

### Rule 2: AL1 vs CO1 — THREE dimensions

**DIMENSION 1 — Surface form:**
- "how to" + action verb → CO1 (procedural recipe)
- "how does" / "why" / "explain" / "what does X mean" → AL1 (conceptual)

**DIMENSION 2 — Conversational context:**
- Student's question probes AI's PREVIOUS response to UNDERSTAND IT DEEPER → AL1
- Standalone question about new topic → default to D1 and D3
- Bounded factual answer about AI's output (yes/no, specific value) → CO1 even in context

**DIMENSION 3 — Answer type:**
- Expected answer is CONCEPTUAL EXPLANATION (mechanism, "because...", multi-sentence) → AL1
- Expected answer is BOUNDED FACT (yes/no, value, list, command, procedure) → CO1
- Applies REGARDLESS of turn position (Turn 1 or later)

**Priority: Context (D2) > Answer Type (D3) > Surface Form (D1)**

Examples:
- "does nat generate acks" (yes/no form, BUT probing AI's networking topic) → **AL1** (D2 wins)
- "what does the star in torch.mean mean?" (Turn 1, answer requires explaining *args) → **AL1** (D1+D3)
- "in cross_val_score do you use training or test set?" (Turn 1, answer requires explaining k-fold) → **AL1** (D3 wins)
- "does this remove the row?" (yes/no about AI's code, answer is literally yes/no) → **CO1** (bounded)
- "if I type 'th' what should be suggested words?" (specific output) → **CO1** (D3: bounded)
- "how to use priority queues for ucs" (how-to procedural) → **CO1** (D1+D3)
- "what is min heap" (standalone definition, brief answer) → **CO1** (D3: bounded)
- "can you give me examples of middleboxes" (in ongoing networking discussion) → **AL1** (D2 wins)

### Rule 3: AL5 vs CO3 — PURPOSE test
- **Key signal**: NOT "does the student paste code?" but "what is the student's PURPOSE?"
  - Paste + STRATEGIC direction (constraints, modifications, approach change) → **AL5**
  - Paste + contextual info that REDIRECTS AI → **AL5**
  - Paste + STUDENT-AUTHORED DETAILED TODO SPECS (method names, algorithms, parameters) → **AL5** (specs ARE direction)
  - Paste + IMPERATIVE task command ("make X", "build Y", "show skeleton") → **CO3**
  - Paste + BLANK TODO ("# TODO", "# TODO: implement") + task request → **CO3**
  - Paste + **VERBATIM assignment TODO specs** → **CO3** (see Rule 9)
  - Paste + error → see **Rule 8**
  - Own code + "is this correct?" → **AL2**
- **TODO specification test**: Read TODO/comment lines. (1) Are they verbatim from the assignment? → CO3. (2) Student-authored specific instructions? → AL5. (3) Blank/generic? → CO3.
- **Critical challenge**: Student challenges AI with evidence or reasoning → **AL5(d)**
  - "you're wrong because..." (with reasoning) → AL5
  - "that's wrong" / "try again" (without reasoning) → CO3

### Rule 4: First-time task vs Undirected retry (both CO3)
Both are coded CO3, but the distinction matters for error traceback handling (Rule 8):
- **First-time task**: Student provides NEW material (code, error, data, task) — even without analysis
- **Undirected retry**: Student provides NO new material, just "try again" / "that didn't work" / "redo"; OR pastes error from running AI's previous code without question/direction
- **Test 1**: Any new information (code, error, data, context)? YES → first-time task pattern.
- **Test 2**: First request or content-free retry?
- **Key**: Pasting an error traceback IS new information → first-time task pattern (unless it's from running AI's previous code with no analysis).

### Rule 5: AL5 vs AL2 — DIRECTION vs VALIDATION
- **AL5**: Student DIRECTS AI's behavior (tells AI how to approach differently, challenges with evidence)
  - "can we use Counter method instead?" → AL5 (directive)
  - "No, [correct information]" → AL5(d) (challenge with correction)
- **AL2**: Student seeks VALIDATION of own work
  - "is my code correct?" → AL2
  - "why doesn't mine work?" → AL2
- **Test**: "do it MY way" (AL5) vs "is my approach right?" (AL2)

### Rule 6: AL2 vs AL1 — OWN WORK test
- **AL2**: Presents OWN work for evaluation/verification/debugging
  - Own code + "is this correct?" → AL2
  - Own code + "why doesn't mine work?" → AL2
  - Expected output + own code + asks why they differ → AL2
- **AL1**: Asks about a GENERAL CONCEPT, even if triggered by own experience
  - "why do values change every time?" → AL1 (about randomness — a concept)
  - "what would the output of this function look like?" → AL1 (about function behavior)
- **Test**: "evaluate MY work" (AL2) vs "explain THIS concept" (AL1)

### Rule 7: AL5 vs CO3 — DIRECTION test (with error/retry)
- **AL5**: Paste + strategic direction, purpose, or evidence-based challenge
- **CO3**: FIRST-TIME task/error (own work, new request) OR undirected retry
  Examples:
  - "here is my code [code] TypeError: '<' not supported..." (first-time) → **CO3**
  - "[error from running AI's previous code]" (no question) → **CO3** (undirected retry)
  - "here is my code [code] I think the error is because Node isn't comparable" → **AL2**
  - "here is my code [code] try using a tuple (cost, id) instead" → **AL5**
  - "try again" / "that didn't work" (no new info) → **CO3** (undirected retry)

### Rule 8: ERROR TRACEBACK HANDLING

When a student pastes error output, the error is NEW INFORMATION. The ACCOMPANYING TEXT determines the code:

| Accompanying text | Context | Code | Reasoning |
|-------------------|---------|------|-----------|
| Error + "why is this happening?" / "what does this mean?" | Any | **AL1** | Seeks conceptual understanding |
| Error + "is my code correct?" / "what's wrong with my approach?" | Any | **AL2** | Evaluates own work |
| Error + "fix this" / imperative command | Any | **CO3** | Delegates fix task |
| Error + NO text, FIRST-TIME task (student's own work) | New task | **CO3** | First-time task delegation |
| Error + NO text, from RUNNING AI'S PREVIOUS code | Retry | **CO3** | Undirected retry (formerly CO4) |
| Error + own analysis ("I think it's because...") | Any | **AL2** | Demonstrates reasoning |
| Error + specific fix direction ("use tuple instead") | Any | **AL5** | Strategic direction |
| Error + challenge ("that can't be right because...") | Any | **AL5** | Critical challenge with evidence |
| NO error, just "try again" / "that didn't work" | Any | **CO3** | Content-free retry |

### Rule 9: VERBATIM ASSIGNMENT PASTE (NEW in v2.1)

When assignment context is provided in the prompt, use it to determine whether the student's pasted material is from the assignment or student-authored:

**VERBATIM PASTE = CO3:**
- Student pastes assignment instructions, README text, starter code cells, or notebook TODO cells with NO or MINIMAL additions of their own
- Even if the assignment text contains "detailed" instructions (e.g., "Use sklearn to train a LogisticRegression model") — if these instructions are FROM THE ASSIGNMENT, the student made no intellectual contribution → CO3
- Student pastes a code cell that is identical to a starter code template (empty function with docstring, class with #TODO) → CO3

**NOT VERBATIM = code by accompanying text:**
- Student pastes assignment material BUT ADDS their own question ("how does this work?") → AL1
- Student pastes assignment material BUT ADDS their own approach/constraints → AL5
- Student writes their own TODO specs that go BEYOND what the assignment asks → AL5
- Student pastes assignment + their own partial implementation → code by the implementation content

**Test**: Would the student's message look the same if they just copy-pasted from the assignment notebook? YES → CO3. NO → code by what the student added.

---

### Rule 10: AL5 vs CO3 — CONTEXT REDIRECTION TEST

**Core principle**: AL5 requires the student to MODIFY or REDIRECT what the AI previously said or produced. A student giving an imperative instruction is NOT automatically CO3 — check whether the instruction responds to and changes the AI's prior output.

**AL5 (strategic redirection)**: The student's message references, corrects, or modifies AI's PREVIOUS response:
- Student changes AI's approach: "can you do it without [X]?" (after AI used X)
- Student corrects AI's assumptions: "my dataframe is called Y, not X" (after AI assumed X)
- Student changes parameters AI used: "prefix = th" (after AI demonstrated with prefix = l)
- Student negates AI's answer and provides own direction: "no, I'm using [X], fix it" (rejects AI's assumption)
- Student adds constraints to AI's previous code: "add [feature] too" (after AI gave partial solution)

**CO3 (task delegation without redirection)**: The student's message does NOT reference or modify AI's previous output:
- First turn of conversation (no prior AI to redirect) → CO3
- Student gives a standalone task: "create X for me" (not modifying anything AI said)
- Student pastes code with only "fix it" (no indication of what AI got wrong)
- Student repeats/rephrases the same request without new direction

**Key test**: Does the student's instruction make sense ONLY in context of AI's previous response? YES → AL5. Could the instruction stand alone without AI's prior message? YES → likely CO3.

---

## 6. EXCLUSION CONDITIONS (per code)

For each code, these conditions mean the turn is NOT this code even if surface features match:

| Code | NOT this code if... |
|------|-------------------|
| OT | Student says "thanks" but continues with learning content in same turn |
| CO1 | Expected answer requires multi-sentence conceptual explanation → AL1 |
| CO1 | Student's question probes AI's topic seeking UNDERSTANDING → AL1 |
| CO1 | Student's question asks for SPECIFIC OUTPUT (yes/no, value) about AI's code → stays CO1 even in context |
| CO2 | Student introduces ANY new information (code, data, errors, questions) → recode |
| CO2 | Student provides own code/data → recode (NOT automatically AL5) |
| CO2 | Student pastes error output → CO3 |
| CO3 | Student provides own COMPLETED code + asks for verification → AL2 |
| CO3 | Student provides own code + specific modification direction → AL5 |
| CO3 | Student asks "how" something works conceptually → AL1 |
| CO3 | Student pastes material + conceptual question (why/how/explain) → AL1 |
| CO3 | Student pastes code with STUDENT-AUTHORED detailed TODO specifications → AL5 |
| CO3 | Student challenges AI with evidence/reasoning → AL5(d) |
| AL1 | Student expects bounded factual answer about standalone topic → CO1 |
| AL1 | Student presents own work for evaluation → AL2 |
| AL2 | Student doesn't include own solution/reasoning → CO1 or AL1 |
| AL2 | Student asks about GENERAL CONCEPT (not evaluating own work) → AL1 |
| AL4 | Student pastes results without connecting to broader concepts → CO3 or AL5 |
| AL5 | Student has no strategic direction — just pastes + imperative → CO3 |
| AL5 | Student pastes code + error + asks "why" → AL1 (wants understanding, not redirection) |
| AL5 | Student pastes own code for verification → AL2 |
| AL5 | Student shares results connecting to concept → AL4 |
| AL5 | "that's wrong" without reasoning → CO3 (undirected retry, no evidence) |
| AL5 | Verbatim assignment paste without student additions → CO3 |

---

## 7. OUTPUT FORMAT

For each student turn in the conversation, output EXACTLY this format:

```
Turn [N]: [CODE] | Confidence: [High/Medium/Low] | Reason: "[one sentence justification]"
```

**Rules:**
- `[N]` = the turn number as provided in the input (1-indexed)
- `[CODE]` = exactly one of: OT, CO1, CO2, CO3, AL1, AL2, AL4, AL5
- Confidence levels:
  - **High** = clear-cut case, no hesitation
  - **Medium** = minor ambiguity but confident in the assignment
  - **Low** = genuine ambiguity between two codes; note the alternative in the Reason
- Reason must:
  - Be exactly ONE sentence
  - Reference the specific behavioral evidence in the turn
  - For Low confidence: mention the alternative code (e.g., "Could also be AL1 — student's intent is ambiguous")
- Code ONLY student turns. Skip AI turns entirely.
- Process ALL student turns in the conversation — do not skip any.
- Do NOT add any text before or after the coding lines.

**Example output:**
```
Turn 1: CO3 | Confidence: High | Reason: "Student pastes complete assignment instructions with #TODO comments, no personal analysis shown."
Turn 2: AL1 | Confidence: Medium | Reason: "Student asks how BFS traversal works conceptually; could also be CO1 but expects multi-sentence explanation."
Turn 3: CO2 | Confidence: High | Reason: "Single-word acknowledgment 'ok' with no engagement with AI's explanation."
```

---

## 8. CONTEXT WINDOW INSTRUCTION

**Input unit = complete conversation.** You receive ALL turns in a conversation at once. This is critical because:
- **AL1 vs CO1** depends on whether the student's question probes AI's previous response AND whether the answer is conceptual or bounded
- **AL5 vs CO3** depends on the PURPOSE of the student's pasted material and whether it's verbatim from the assignment
- **AL2 vs AL1** depends on whether the student is presenting own work vs asking about a concept
- **CO2** requires confirming no new information is introduced (context needed)
- CO3 (undirected retry) requires knowing what AI previously produced
- AL5(d) (critical challenge) requires seeing what AI claimed to evaluate the challenge

Process turns sequentially (Turn 1 → Turn 2 → ...) but use the full conversation context for each coding decision. **Always read AI's previous response before coding the student turn.**

---

## 9. FEW-SHOT EXAMPLES

### AL1 vs CO1 — Context-dependent coding + Answer Type

**Example AL1-1: Follow-up probing AI's explanation (yes/no form → AL1 by context)**
AI_Previous_Response: [Long explanation about IP addresses, host bits, network structure, and subnet masks]
Student_Message: "does nat generate acks"
Code: AL1
Reasoning: Although this is a yes/no surface form (which would suggest CO1), the student is continuing to explore networking concepts that AI introduced in its previous response. The question probes deeper into AI's teaching domain — it's engaging with AI's explanation, not a standalone factual query.

**Example AL1-2: Exploring a category AI introduced**
AI_Previous_Response: [AI listed examples of middleboxes including firewalls, load balancers, NAT devices, etc.]
Student_Message: "is an http load balancer a middlebox"
Code: AL1
Reasoning: "Middlebox" is a concept AI explicitly discussed in its previous response. The student is probing AI's categorization to deepen understanding — engaging with AI's output, not asking a standalone question.

**Example AL1-3: "What about X?" continuing AI's topic**
AI_Previous_Response: [AI confirmed HTTP load balancer is a middlebox with detailed explanation]
Student_Message: "what about an http cache"
Code: AL1
Reasoning: Student continues exploring AI's middlebox topic by asking about another item. This follow-up only makes sense in context of AI's prior explanation.

**Example AL1-4: Asking about specific element from AI's code**
AI_Previous_Response: [AI showed code using dict(table) in a frequency table function]
Student_Message: "dict(table) what does it do?"
Code: AL1
Reasoning: dict(table) appeared in AI's code output. Student is seeking to understand a specific part of AI's explanation — "opening AI's black box."

**Example AL1-5: Turn-1 conceptual question → AL1 by answer type**
AI_Previous_Response: [Conversation Start]
Student_Message: "what does the star in the torch.mean parameters mean?"
Code: AL1
Reasoning: Even though this is Turn 1 with no prior AI context, the student asks about the MEANING of a syntax element (*args). The answer requires explaining Python's argument unpacking concept — a multi-sentence conceptual explanation, not a bounded fact. Answer type = conceptual → AL1.

**Example AL1-6: Turn-1 "how does X work" → AL1 by answer type**
AI_Previous_Response: [Conversation Start]
Student_Message: "in cross_val_score do you use training set or test set"
Code: AL1
Reasoning: Although this looks like a yes/no question at Turn 1, the correct answer requires explaining the k-fold cross-validation MECHANISM (it creates its own splits). The expected answer is a conceptual explanation, not "training set" or "test set." Answer type = conceptual → AL1.

**Example AL1-7: "Examples of X" in ongoing topic → AL1 by context**
AI_Previous_Response: [AI discussed networking architecture, middleboxes, and network layers]
Student_Message: "can you give me a few examples of middleboxes in networking"
Code: AL1
Reasoning: The student asks for examples of a concept (middleboxes) that is central to AI's ongoing explanation. The request for examples serves to deepen understanding of the concept AI introduced — this is probing AI's teaching domain, not a standalone factual query.

**Example CO1-1: Standalone definition request**
AI_Previous_Response: [AI explained priority queues and UCS algorithm]
Student_Message: "what is min heap"
Code: CO1
Reasoning: Although AI mentioned related concepts, "what is min heap" is a standalone definition request that could be answered with a brief bounded definition. This is a direct factual query, not probing AI's explanation.

**Example CO1-2: Standalone question at conversation start**
AI_Previous_Response: [Conversation Start]
Student_Message: "what are host bits used for in an ip address"
Code: CO1
Reasoning: First turn with no prior AI context. Student asks a direct factual question expecting a bounded answer — the answer is a specific fact about IP addressing, not a multi-sentence conceptual explanation.

**Example CO1-3: Procedural how-to question**
AI_Previous_Response: [AI provided complete step-by-step code implementation]
Student_Message: "How can I approach the final reports section?"
Code: CO1
Reasoning: Student asks a procedural question about how to do something, expecting guidance — not probing AI's previous code explanation.

**Example CO1-4: Bounded factual question about AI's output → CO1**
AI_Previous_Response: [AI provided code that processes a dataframe]
Student_Message: "does this remove the row"
Code: CO1
Reasoning: Student asks a yes/no factual question about what AI's code does. This expects a bounded answer ("yes" or "no"), not a conceptual explanation. Even though it refers to AI's output, the answer type is bounded → CO1.

**Example CO1-5: Specific output question → CO1**
AI_Previous_Response: [AI explained BFS implementation with a trie data structure]
Student_Message: "if I type in 'th' what should be the suggested words in order?"
Code: CO1
Reasoning: Student asks for a specific expected output — a concrete list. This is a bounded factual answer, not a conceptual explanation of how BFS works. Answer type = bounded → CO1.

**Example CO1-6: "How to use X" = procedural → CO1**
AI_Previous_Response: [AI explained UCS algorithm conceptually]
Student_Message: "how to use priority queues for ucs"
Code: CO1
Reasoning: "How to use X for Y" is a procedural how-to request expecting implementation steps, not a conceptual explanation of why/how the mechanism works. Answer type = procedure → CO1.

### AL5 — Strategic prompting (PURPOSE matters)

**Example AL5-1: Providing own material WITH redirection**
AI_Previous_Response: [AI explained how to load CSV from remote URL with code examples]
Student_Message: "its downloaded into my files in vscode"
Code: AL5
Reasoning: Student provides contextual information that REDIRECTS AI's approach — telling AI the file is local, not remote. This shapes AI's next response strategically.

**Example AL5-2: Directive modification ("not X, just Y")**
AI_Previous_Response: [AI displayed equation in LaTeX format]
Student_Message: "Not in latex, just as a math equation"
Code: AL5
Reasoning: Student specifies output constraint with clear direction: reject one format, request alternative. This is directive modification of AI's output approach.

**Example AL5-3: Suggesting alternative approach**
AI_Previous_Response: [AI showed complex frequency table implementation using defaultdict]
Student_Message: "can we just use the counter method"
Code: AL5
Reasoning: Student proposes an alternative approach (Counter class) to modify AI's implementation. This is evaluative modification that redirects AI's approach based on student's own thinking.

**Example AL5-4: Providing own data with contextual purpose**
AI_Previous_Response: [AI explained how to split data into features and labels]
Student_Message: "# Column Non-Null Count Dtype\n--- ------ -------------- -----\n 0 Temperature °C 1000 non-null int64\n 1 Mols KCL 1000 non-null int64..."
Code: AL5
Reasoning: Student provides their own data output that REDIRECTS AI's approach — showing the actual column structure so AI uses correct column names. This strategically shapes AI's next response.

**Example AL5-5: Redirection via constraint ("keep in mind")**
AI_Previous_Response: [AI produced pandas code using 'Target' as column name]
Student_Message: "Keep in mind the column names from your previous output, 'Target' is not a column name"
Code: AL5
Reasoning: Student redirects AI's approach by providing a specific constraint (correct column names). This is directive modification — pointing out the error AND specifying what to change. Not just undirected retry (CO3) but redirecting.

**Example AL5-6: Critical challenge with evidence (formerly AL3)**
AI_Previous_Response: [AI provided a generic report structure for RNN assignment]
Student_Message: "No, this is the final reports section: ## TODO: Fill out your Final Report here\nHow many late days are you using..."
Code: AL5
Reasoning: Student contradicts AI's output ("No") and provides the correct information (actual report template) as evidence. This is a critical challenge — the student presents evidence that AI's output is wrong, which constitutes AL5(d).

### CO3 — Task outsourcing (INCLUDING retry and verbatim paste)

**Example CO3-1: Action request as question**
AI_Previous_Response: [Conversation Start]
Student_Message: "Hi! Can you go to assignment 3 and its contents"
Code: CO3
Reasoning: Student asks AI to DO something (navigate to assignment content) — this is task delegation even though phrased as a question.

**Example CO3-2: Format conversion request**
AI_Previous_Response: [AI showed polynomial regression equation with explanation]
Student_Message: "give me that in LaTeX"
Code: CO3
Reasoning: Student requests AI to produce a deliverable (LaTeX formatted equation). This is delegation of a formatting task.

**Example CO3-3: Pasting data + imperative "make X" → CO3**
AI_Previous_Response: [Conversation Start]
Student_Message: "coefficients [1.2e+01, -1.27e-07, ...] intercept 2.05e-05\n\nmake an equation out of this"
Code: CO3
Reasoning: Student pastes raw output data + imperative command "make an equation." The pasted material is raw INPUT for AI to process — the student adds no strategic direction. PURPOSE = delegation → CO3, not AL5.

**Example CO3-4: Empty template code + "show skeleton code" → CO3**
AI_Previous_Response: [Conversation Start]
Student_Message: "def create_frequency_tables(document, n):\n  \"\"\"[docstring]...\"\"\"\n  return\n\nshow the skeleton code"
Code: CO3
Reasoning: The pasted function is essentially empty (just signature + docstring + bare return). Student contributes no real implementation, and "show the skeleton code" is a task request. The "code" is a template, not intellectual contribution → CO3.

**Example CO3-5: Template class + "implement BFS" → CO3**
AI_Previous_Response: [Conversation Start]
Student_Message: "I am trying to implement BFS in python. Below is the current definition for the node class, but it can be changed how you see fit:\n  class Node:\n  #TODO\n  def __init__(self):\n    self.children = {}"
Code: CO3
Reasoning: The Node class is a near-empty template (TODO, minimal __init__). "Can be changed how you see fit" explicitly delegates all decisions to AI. Despite pasting code, there's no intellectual contribution → CO3.

**Example CO3-6: Terse noun-phrase → CO3**
AI_Previous_Response: [AI provided DFS code and explanation]
Student_Message: "stack based lifo"
Code: CO3
Reasoning: This terse noun-phrase fragment is an implicit task request (asking AI to implement stack-based LIFO), not a conceptual question. No question word (why/how/what does X mean) → CO3.

**Example CO3-7: Verbatim assignment notebook paste → CO3**
AI_Previous_Response: [Conversation Start]
Student_Message: "## Part 3: Logistic Regression\n# TODO -- Use logistic regression to predict the probabilities of each class\n# then find the score of the model\n# Also find the coefficients and intercepts of the logistic regression model"
Code: CO3
Reasoning: Student pastes a cell VERBATIM from the assignment notebook — these are assignment-provided TODO instructions, not student-authored specifications. The student made no intellectual contribution → CO3.

**Example CO3-8: Undirected retry → CO3 (formerly CO4)**
AI_Previous_Response: [AI provided code that student tried but it didn't work]
Student_Message: "that didn't work, try again"
Code: CO3
Reasoning: Student says "try again" without providing any new information — no error traceback, no code, no specifics about what went wrong. Content-free undirected retry → CO3.

**Example CO3-9: Undirected error dump from AI's code → CO3 (formerly CO4)**
AI_Previous_Response: [AI provided code for training ML model with sample prediction]
Student_Message: "/home/codespace/.local/lib/python3.12/site-packages/sklearn/base.py:493: UserWarning: X does not have valid feature names, but LinearRegression was fitted with feature names\n  warnings.warn("
Code: CO3
Reasoning: Student ran AI's previous code, got a warning, and pastes it back without any question, analysis, or direction. This is an undirected retry — the error comes from running AI's code. → CO3.

**⚠️ CONTRAST — these are NOT CO3:**
- Error + "why is this happening?" / conceptual question → **AL1** (seeks understanding)
- Error + "is my code correct?" → **AL2** (evaluates own work)
- Error + evidence-based challenge ("that can't be right because...") → **AL5** (critical challenge)
See §5 Rule 8 for complete error traceback handling.

### AL2 — Self-monitoring (presenting own work for verification)

**Example AL2-1: Own code + "is this correct?" → AL2**
AI_Previous_Response: [AI explained DFS implementation]
Student_Message: "[Student's complete DFS implementation code]\nis this correct"
Code: AL2
Reasoning: Student presents their OWN completed code and asks for verification. This is self-monitoring — submitting own work for evaluation, not strategic prompting.

**Example AL2-2: Own code + "why doesn't this work?" → AL2**
AI_Previous_Response: [AI explained BFS algorithm and expected output]
Student_Message: "The order of the words for BFS should be: [the, thee, thou...]. My implementation (below) does not return suggestions in that order, could you help figure out why?\n[student's suggest_bfs code]"
Code: AL2
Reasoning: Student states expected output, provides own implementation, and identifies a discrepancy ("does not return in that order"). This is active debugging — self-monitoring their own work's behavior, not strategic prompting.

### AL4 — Knowledge integration (connecting own results)

**Example AL4-1: Sharing own results after concept discussion → AL4**
AI_Previous_Response: [AI explained what cross-validation is conceptually]
Student_Message: "Cross-validation scores: [0.839, 0.871, 0.859, 0.872, 0.844]\nMean cross-validation score: 0.857"
Code: AL4
Reasoning: Student shares their OWN experimental cross-validation results right after asking "what is cross validation." They are CONNECTING their own experimental output to the concept AI just explained — knowledge integration, not strategic prompting.

---

## 10. GOLD STANDARD BASE RATES

Target distribution from 320-turn gold standard (8-code system, after gold revision):

| Code | N | % |
|------|---|---|
| CO3 | 126 | 39.4% |
| CO1 | 66 | 20.6% |
| AL1 | 61 | 19.1% |
| AL5 | 32 | 10.0% |
| AL2 | 28 | 8.8% |
| OT | 4 | 1.2% |
| CO2 | 2 | 0.6% |
| AL4 | 1 | 0.3% |

**CO total: 60.6% | AL total: 38.1% | OT: 1.2%**

If your output distribution deviates significantly from these base rates (χ² test, p < 0.05), flag for human review.

---

*End of Codebook v2.2*
