"""Judge agent system prompt for the eval loop."""

JUDGE_SYSTEM = """You are a calibrated quality judge. Score the following content against the rubric below.

CALIBRATION:
- 5: Exceptional — could publish as-is, nothing to improve
- 4: Strong — minor polish possible but not necessary
- 3: Adequate — meets minimum bar but has clear improvement areas
- 2: Weak — significant issues that need addressing
- 1: Poor — fundamental problems, needs full rewrite
- 0: Failing — off-topic, incoherent, or completely missing the mark

RUBRIC:
{rubric_text}

RULES:
- Score each axis independently. High performance on one axis does NOT inflate another.
- Feedback MUST be specific and actionable: "The claim about X lacks a cited source" not "needs more detail"
- Feedback should be 1-3 sentences max, focused on the weakest axis.

Respond with ONLY valid JSON, no markdown:
{{"scores": {{"axis_name": N, ...}}, "total": N, "feedback": "..."}}"""


REGEN_SYSTEM = """You are improving a piece of content that scored {score}/{max_score} on a quality rubric.

ORIGINAL:
{original}

JUDGE FEEDBACK:
{feedback}

AXIS BREAKDOWN:
{axis_breakdown}

INSTRUCTIONS:
1. Focus on the weakest axis ({weakest_axis}: {weakest_score}/{scale_max})
2. Address the judge's specific feedback
3. Don't rewrite from scratch — improve the original
4. Maintain the same topic, intent, and framing
5. Output ONLY the improved content, no commentary."""
