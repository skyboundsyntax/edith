from backend.app.intelligence.query_planner import parse_job_query_to_spec
from backend.app.intelligence.role_matcher import is_matching_role


def test_game_developer_query_rejects_generic_developer_roles():
    query_spec = parse_job_query_to_spec("game developer").model_dump()

    assert is_matching_role("Game Developer", query_spec)
    assert is_matching_role("Junior Game Developer", query_spec)
    assert is_matching_role("Gameplay Programmer", query_spec)
    assert is_matching_role("Unity Developer", query_spec)
    assert not is_matching_role("Junior Developer", query_spec)
    assert not is_matching_role("Junior Software Engineer", query_spec)
    assert not is_matching_role("Frontend Developer", query_spec)


def test_unconstrained_query_still_accepts_job_titles():
    assert is_matching_role("Junior Developer", {})


def test_role_matching_ignores_description_word_overlap():
    query_spec = parse_job_query_to_spec("game developer").model_dump()

    assert not is_matching_role(
        "Junior Developer",
        query_spec,
        description="Works with game development and Unity.",
    )
