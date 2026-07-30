from dataclasses import dataclass
from typing import Callable, List, Tuple
 
from src.recommender import UserProfile, load_songs, recommend
 
 
@dataclass
class EvalCase:
    name: str
    profile: UserProfile
    top_k: int
    check: Callable[[list, list], Tuple[bool, str]]
 
 
def confidence(scored) -> float:
    """Heuristic confidence score: how much the top pick beats the
    runner-up, normalized to 0-1. A low margin means the system's
    top recommendation isn't meaningfully better than the alternative.
    """
    if len(scored) < 2:
        return 1.0
    margin = scored[0].total - scored[1].total
    return round(max(0.0, min(1.0, margin / 5.0)), 2)
 
 
def check_genre_and_mood_match(scored, warnings) -> Tuple[bool, str]:
    top = scored[0]
    ok = top.genre_points == 2.0 and top.mood_points == 1.0
    detail = f'top pick "{top.song.title}" — genre_points={top.genre_points}, mood_points={top.mood_points}'
    return ok, detail
 
 
def check_genre_match_only(scored, warnings) -> Tuple[bool, str]:
    top = scored[0]
    ok = top.genre_points == 2.0
    detail = f'top pick "{top.song.title}" — genre_points={top.genre_points} (mood disabled by fallback)'
    return ok, detail
 
 
def check_fallback_triggered(scored, warnings) -> Tuple[bool, str]:
    ok = len(warnings) > 0 and len(scored) > 0
    detail = f"{len(warnings)} warning(s) logged, {len(scored)} result(s) still returned"
    return ok, detail
 
 
def check_no_crash_on_oversized_top_k(scored, warnings) -> Tuple[bool, str]:
    ok = 0 < len(scored) <= 20
    detail = f"{len(scored)} results returned for a top_k request larger than the catalog"
    return ok, detail
 
 
CASES: List[EvalCase] = [
    EvalCase(
        "Rock/Intense — exact genre+mood match available",
        UserProfile("rock", "intense", 0.85), 3, check_genre_and_mood_match,
    ),
    EvalCase(
        "Lofi/Chill — exact genre+mood match available",
        UserProfile("lofi", "chill", 0.25), 3, check_genre_and_mood_match,
    ),
    EvalCase(
        "Jazz/Euphoric — mood not in catalog (partial fallback)",
        UserProfile("jazz", "euphoric", 0.4), 3, check_genre_match_only,
    ),
    EvalCase(
        "Flamenco/Passionate — genre AND mood not in catalog (full fallback)",
        UserProfile("flamenco", "passionate", 0.7), 3, check_fallback_triggered,
    ),
    EvalCase(
        "Oversized top_k request (50 on a 20-song catalog)",
        UserProfile("pop", "happy", 0.8), 50, check_no_crash_on_oversized_top_k,
    ),
]
 
 
def main():
    songs = load_songs("data/songs.csv")
    results = []
 
    for case in CASES:
        try:
            scored, warnings = recommend(songs, case.profile, top_k=case.top_k)
            passed, detail = case.check(scored, warnings)
            conf = confidence(scored)
            results.append((case.name, passed, detail, conf))
        except Exception as e:
            results.append((case.name, False, f"CRASHED: {e}", 0.0))
 
    print("=" * 72)
    print("EVALUATION SUMMARY")
    print("=" * 72)
    passed_count = 0
    for name, passed, detail, conf in results:
        status = "PASS" if passed else "FAIL"
        if passed:
            passed_count += 1
        print(f"[{status}] {name}")
        print(f"       detail:     {detail}")
        print(f"       confidence: {conf}")
        print()
 
    total = len(results)
    avg_conf = round(sum(c for _, _, _, c in results) / total, 2)
    print("-" * 72)
    print(f"Result: {passed_count}/{total} cases passed")
    print(f"Average confidence: {avg_conf}")
    print("=" * 72)
 
 
if __name__ == "__main__":
    main()