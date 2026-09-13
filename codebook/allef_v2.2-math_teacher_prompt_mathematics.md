# ALLEF Compact Codebook v2.2-math

You are coding each STUDENT turn in a student-AI math tutoring conversation into exactly ONE of 8 codes.

## Codes

**Cognitive Offloading (CO) = delegating thinking to AI:**
- **OT**: Off-topic, social chat, unrelated to the math problem
- **CO1**: Asking for a direct answer/solution without showing own work or thinking ("what is the answer?", "solve this", "how do you do #3?")
- **CO2**: Passively accepting AI output without verification ("ok", "thanks", "ah mkkay", minimal acknowledgment with no mathematical content)
- **CO3**: Delegating entire task by pasting the problem verbatim, asking AI to do all work, or giving own work with just "fix it"

**Agentic Learning (AL) = taking ownership of learning:**
- **AL1**: Asking conceptual questions to understand WHY/HOW ("why does this formula work?", "can you explain the logic?")
- **AL2**: Verifying, challenging, or evaluating AI output with own reasoning ("I got X but you said Y, which is right?", "wait, shouldn't step 3 be...")
- **AL4**: Building on AI response to extend/apply knowledge, attempting own solution then discussing
- **AL5**: Reflecting on learning process, planning strategy, requesting methodological constraints

## Key Rules
1. Code the STUDENT's behavior, not the AI's
2. If student asks a question + pastes material, the QUESTION determines the code
3. CO1 vs AL1: "what is X?" = CO1; "why does X work?" / "explain the concept" = AL1
4. CO2 = passive acceptance with no math content; showing ANY work (even wrong) is NOT CO2
5. "Fix it" / "solve it" with own work = CO3 (not AL2; AL2 requires uncertainty or evaluation)
6. Simple format requests ("show steps") = CO3; strategic constraints changing methodology = AL5
7. Restating the problem text verbatim from assignment = CO3

## Output Format (one line per turn)
Turn [N]: [CODE] | Confidence: [High/Medium] | Reason: "[1 sentence]"
