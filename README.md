# Rule-Based Music Recommender

## Original Project (Modules 3)
This project began as a **rule-based music recommendation engine** built in Modules 1–3. Its original goal was to take a small song catalog (`songs.csv`) and a user "taste profile," score every song against that profile using a weighted point system, and return a ranked top-K list of recommendations. The original scope focused on getting the scoring math right and understanding how small design choices (like feature weighting) shape recommendation behavior.

## Title and Summary
**MoodDialr** is a lightweight, explainable recommendation system. Instead of a black-box model, it uses a transparent point-based scoring formula, so every recommendation can be traced back to *why* it was ranked where it was. This matters because the assignment's goal isn't just "does it recommend songs" — it's "can you explain and defend the logic behind those recommendations."

## Architecture Overview
The data flow is a simple three-stage pipeline:

```
Input (User Taste Profile + songs.csv)
        ↓
Process: for each song → compute score
   +2.0  if genre matches user's favorite genre
   +1.0  if mood matches user's favorite mood
   +up to 2.0 for energy similarity:
        2.0 * (1 - abs(song.energy - user.target_energy))
        ↓
Output: sort all songs by total score, descending → return top K
```

Each song is judged independently in a single loop — there's no cross-song comparison until the final sort step. This keeps the logic easy to unit test, since each song's score can be checked in isolation. The scoring/ranking logic lives in `src/recommender.py`; `src/main.py` is the thin CLI entry point.

## Setup Instructions
1. Clone the repo and enter it:
   ```bash
   git clone https://github.com/Robert-Tenney/applied-ai-system-project.git
   cd applied-ai-system-project
   ```
2. (Optional) Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Mac/Linux
   .venv\Scripts\activate         # Windows
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the app from the project root:
   ```bash
   python -m src.main --profile rock_intense --top 3
   ```
5. Adjust `--profile` (see `src/recommender.py` → `PRESET_PROFILES`) or `--top` to test different taste combinations.

## Sample Interactions
The following are actual captured runs of `recommender.py` against `data/songs.csv` (a 20-song catalog).

**Example 1 — Rock/Intense profile**
```
$ python -m src.main --profile rock_intense --top 3
User profile: {favorite_genre: rock, favorite_mood: intense, target_energy: 0.85}

Rank 1: "Thunder Circuit" — Voltline
  genre match: +2.0 | mood match: +1.0 | energy sim: +1.92 | TOTAL: 4.92
Rank 2: "Storm Runner" — Voltline
  genre match: +2.0 | mood match: +1.0 | energy sim: +1.88 | TOTAL: 4.88
Rank 3: "Gym Hero" — Max Pulse
  genre match: +0.0 | mood match: +1.0 | energy sim: +1.84 | TOTAL: 2.84
```
Note "Gym Hero" (mood match only — its genre is "pop," not "rock") still lands close to the top two purely on a strong energy match — a concrete illustration of the genre-dominance bias described below.

**Example 2 — Chill/Lofi profile**
```
$ python -m src.main --profile lofi_chill --top 3
User profile: {favorite_genre: lofi, favorite_mood: chill, target_energy: 0.25}

Rank 1: "Rainy Shelf" — Paper Lanterns
  genre match: +2.0 | mood match: +1.0 | energy sim: +1.84 | TOTAL: 4.84
Rank 2: "Library Rain" — Paper Lanterns
  genre match: +2.0 | mood match: +1.0 | energy sim: +1.80 | TOTAL: 4.80
Rank 3: "Late Night Pages" — LoRoom
  genre match: +2.0 | mood match: +1.0 | energy sim: +1.74 | TOTAL: 4.74
```

**Example 3 — Guardrail case: genre and mood not in catalog**
```
$ python -m src.main --profile flamenco_passionate --top 3
User profile: {favorite_genre: flamenco, favorite_mood: passionate, target_energy: 0.7}
[WARN] No songs match genre 'flamenco'.
[WARN] No songs match mood 'passionate'.
[WARN] Falling back to remaining scoring criteria only.

Rank 1: "Skyline Bloom" — Indigo Parade
  genre match: +0.0 | mood match: +0.0 | energy sim: +1.92 | TOTAL: 1.92
Rank 2: "Night Drive Loop" — Neon Echo
  genre match: +0.0 | mood match: +0.0 | energy sim: +1.90 | TOTAL: 1.90
Rank 3: "Rooftop Lights" — Indigo Parade
  genre match: +0.0 | mood match: +0.0 | energy sim: +1.88 | TOTAL: 1.88
```
This shows the system degrading gracefully — logging clear warnings and falling back to whichever criteria actually exist in the catalog — instead of crashing or silently returning an empty/misleading list.

## Design Decisions
- **Weighting genre (2.0) above mood (1.0):** chosen because genre felt like the "harder" filter (rock fan rarely wants ambient), while mood is more of a fine-tuner. Trade-off: a great mood match can be buried under a merely-okay genre match.
- **Linear energy similarity formula:** simple and easy to reason about, but it doesn't sharply reward *exact* matches — a song 0.05 off and a song 0.15 off score only slightly differently.
- **Single-value profile (one genre, one mood) vs. list-based:** discussed with my AI coding assistant during design (see `model_card.md`) — a single-value profile is simpler to score but can't represent someone who likes both "intense rock" and "chill lofi" simultaneously. I kept single-value for this version to keep the scoring loop simple, noting it as a known limitation rather than solving it in this iteration.
- **Graceful fallback over hard failure:** if a genre/mood isn't in the catalog, the system logs a warning and reduces to the remaining criteria rather than crashing or returning an empty list.

## Testing Summary
**12 out of 12 automated unit tests passed** (`tests/test_recommender.py`), covering: exact genre/mood matches, no-match scoring, energy similarity at zero distance and at a large distance, the unknown-genre/mood fallback path, top-K slicing, and error handling for missing/empty/malformed CSV files. All test songs are pulled directly from `data/songs.csv`. Run with:
```bash
pytest
```
Actual output (via `python -m unittest tests.test_recommender -v`):
```
test_empty_csv_raises_clear_error ... ok
test_malformed_row_raises_clear_error ... ok
test_missing_file_raises_clear_error ... ok
test_best_match_ranks_first ... ok
test_top_k_returns_requested_count ... ok
test_unknown_genre_does_not_crash_and_ranks_by_energy ... ok
test_unknown_genre_triggers_fallback_warning ... ok
test_energy_similarity_at_large_distance ... ok
test_energy_similarity_at_zero_distance ... ok
test_exact_genre_and_mood_match ... ok
test_no_match_song_scores_zero_on_genre_and_mood ... ok
test_score_genre_false_ignores_genre_even_on_match ... ok

Ran 12 tests in 0.005s

OK
```
The main reliability weakness found during testing: songs with energy values within ~0.05 of each other produce nearly identical scores (see "Gym Hero" in Example 1 above), which can make close calls feel arbitrary — see `model_card.md` for what this taught me.

> Note: the reflection on responsible-AI collaboration, system limitations, and misuse considerations lives in **`model_card.md`**, not here, per the assignment's rubric.