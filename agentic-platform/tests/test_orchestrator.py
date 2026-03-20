def test_orchestrator_graph():
    from app.orchestrator.graph import OrchestrationGraph

    g = OrchestrationGraph()
    g.add_node("n1", {"x": 1})
    assert g.get_node("n1")["x"] == 1
