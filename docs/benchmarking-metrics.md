## Benchmark metrics and scoring

This repo evaluates an adaptive tutoring loop over turns \(t = 1..T\).
Each turn records:

- \(d_t \in \{1,2,3,4,5\}\): question difficulty (LLM-judged)
- \(c_t \in \{0,1\}\): whether the student answered correctly
- `subtopics`: list of subtopic ids associated to the question (multi-label)

### Difficulty-weighted proficiency

We don’t want “accuracy” to be dominated by easy questions, so we weight by difficulty:

\[
P = \frac{\sum_{t=1}^{T} c_t d_t}{\sum_{t=1}^{T} d_t}
\]

This is in \([0,1]\). It’s computed in `benchmark/metrics/metrics.py` (`weighted_proficiency`).

### Proficiency shaping (the “sweet spot”)

Raw \(P\) being too high can mean the system stayed too easy; too low can mean it over-shot difficulty.
To reward keeping the user in an “optimal challenge” band, we shape \(P\) with a Gaussian:

\[
G(P) = \exp\left(-\frac{(P-0.75)^2}{2\sigma^2}\right), \quad \sigma=0.2
\]

So the best score happens near \(P \approx 0.75\), and it falls off when the session is too easy/hard.
Implemented in `benchmark/metrics/score_calculator.py`.

### Error sensitivity

After a wrong answer, we expect the agent to react (usually by lowering difficulty).
Let \(E\) be the indices where \(c_t = 0\). We define:

\[
S = \frac{|\{t \in E \mid d_{t+1} < d_t\}|}{|E|}
\]

If there are no errors, we return \(S=1.0\) by convention. Implemented in `benchmark/metrics/metrics.py`
(`error_sensitivity`).

### Coverage and remediation (topic-level)

We build a per-topic history from the multi-label `subtopics` per turn (see
`benchmark/metrics/coverage_metrics.py`).

Because a single question can touch multiple subtopics, we use a conservative “coverage capacity”:

\[
C = \min(N_{topics}, \lceil 2T \rceil)
\]

Intuition: in \(T\) turns, you can realistically cover at most ~2 distinct topics per turn.

We then compute:

- **Syllabus exposure**: attempted topics / \(C\)
- **Effective curriculum coverage (ECC)**: topics with at least one correct attempt / \(C\)
- **Remediation efficiency**: among topics that were wrong on first encounter, the fraction that are later answered correctly

### Final score (0–100)

Objective metrics are combined as a weighted sum:

\[
Score = 100 \cdot (0.35 \cdot ECC + 0.30 \cdot R + 0.20 \cdot G(P) + 0.15 \cdot S)
\]

Implemented in `benchmark/metrics/score_calculator.py`.
