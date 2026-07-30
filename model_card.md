Model Card: MoodDial
Limitations and Biases
Genre-dominant weighting: genre matches are worth 2x a mood match, so the system can rank a genre-correct-but-mood-wrong song above a song that's a near-perfect emotional fit. This is a design choice, not a bug, but it means the recommender reflects my assumption about what matters more — not a neutral or "correct" ordering.
Single-value taste profile: the profile only stores one favorite genre and one favorite mood. Real listeners have overlapping, situational tastes (e.g., rock in the morning, lofi while studying), and this system can't represent that without running it multiple times with different profiles.
No artist diversity control: the scoring loop judges songs independently, so if several songs by the same artist all score well, the top-K list could be dominated by one artist with no variety.
Linear energy formula: because similarity decays linearly, the system doesn't meaningfully distinguish "close" from "exact" energy matches, which can make near-ties feel somewhat arbitrary in the output.
Potential Misuse and Mitigations

This is a small, catalog-based recommender with no user data collection, so the misuse surface is limited, but a few things are worth naming:

Overstating personalization: because the scoring is fully rule-based and transparent, it would be misleading to present it as a "smart" or "learned" system — it's a weighted filter, not a model that adapts to behavior. The README documents the exact scoring formula for this reason.
Reinforcing narrow taste: a recommender that always favors one genre/mood pairing could narrow, rather than expand, what a user listens to. A simple mitigation would be occasionally injecting a lower-scoring but diverse pick into the top-K list, which I noted as a possible future improvement rather than implementing here.
What Surprised Me During Reliability Testing

The energy similarity formula behaved more "flat" than expected — I assumed a 0.05 gap and a 0.15 gap in energy would produce visibly different rankings, but because the formula is linear and only worth up to 2.0 points total, the difference in score was small enough that genre and mood matches usually decided the outcome anyway. This made me realize the energy feature was doing less work in the final ranking than I'd designed it to.

Building evaluate.py (a standalone end-to-end evaluation harness, separate from the unit tests) surfaced something I hadn't noticed from the unit tests alone: across every test scenario, the confidence margin between the top pick and the runner-up was consistently near-zero (0.0–0.01 on a 0–1 scale). The system was always technically correct, but rarely decisively correct — a direct symptom of the catalog containing multiple similar songs (same genre/mood, close energy) from the same artist. This told me that "passes the test" and "makes a confident recommendation" are two different bars, and my current scoring formula only clears the first one.

Future Improvements
Represent multiple tastes per user instead of a single genre/mood value, so the profile can express "rock when working out, lofi when studying" without needing separate runs (raised directly by the AI critique below).
Add artist-diversity control to the ranking step, so a user doesn't get multiple picks from the same artist crowding out the top-K list.
Widen the energy similarity curve (e.g. quadratic instead of linear) so close-but-not-equal energy matches are rewarded more sharply, addressing the low-confidence-margin finding from evaluate.py.
Incorporate the unused features already in the catalog (tempo, danceability, valence, acousticness) into the scoring formula, since they're currently loaded but ignored.
AI Collaboration

Helpful suggestion: When I asked my AI coding assistant to critique my initial user profile (single genre, single mood, single energy target), it pointed out that this structure couldn't represent someone who likes both "intense rock" and "chill lofi" — it would force an either/or choice. That critique directly shaped the limitations section above and made me document the trade-off explicitly instead of assuming the profile was fine as-is.

Flawed suggestion: Early on, when I asked for a point-weighting strategy, one suggestion was to weight genre, mood, and energy roughly equally (around 1.5–1.7 points each). When I tried this, ties became extremely common in a small 15–20 song catalog, since so many songs could rack up similar totals — it made the "top" recommendation feel more like a coin flip than a ranking. I ended up overriding this and deliberately weighting genre higher, which produced more decisive, explainable rankings, even though it introduced the genre-dominance bias noted above.