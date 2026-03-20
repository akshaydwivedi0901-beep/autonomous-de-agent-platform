def test_agents_imports():
    from app.agents.ba_agent import BAAgent
    from app.agents.planner_agent import PlannerAgent

    assert BAAgent().analyze({})["analysis"] == "stub"
    assert isinstance(PlannerAgent().plan("x"), dict)
