"""Tests for dependency graph and topological sorting."""

from data_cataloger.schema.dependency import DependencyGraph


def test_simple_dependency_chain() -> None:
    """Test simple linear dependency chain."""
    graph = DependencyGraph()
    graph.add_table("A", [])
    graph.add_table("B", ["A"])
    graph.add_table("C", ["B"])

    ordered, cycle = graph.get_processing_order()

    assert cycle is None, "Should not detect cycle in linear chain"
    assert ordered == ["A", "B", "C"], "Should order independent table first"


def test_parallel_independent_tables() -> None:
    """Test parallel independent tables processed before dependent table."""
    graph = DependencyGraph()
    graph.add_table("users", [])
    graph.add_table("products", [])
    graph.add_table("orders", ["users", "products"])

    ordered, cycle = graph.get_processing_order()

    assert cycle is None, "Should not detect cycle"
    assert len(ordered) == 3, "Should include all three tables"
    # users and products can be in any order but must come before orders
    assert ordered[2] == "orders", "orders should be last (depends on both)"
    assert set(ordered[:2]) == {
        "users",
        "products",
    }, "users and products should be first (independent)"


def test_self_referencing_table() -> None:
    """Test self-referencing table (hierarchical structure)."""
    graph = DependencyGraph()
    graph.add_table("categories", ["categories"])  # parent_id FK to same table

    ordered, cycle = graph.get_processing_order()

    assert cycle is None, "Self-referencing should NOT be treated as cycle"
    assert ordered == ["categories"], "Should include categories in order"


def test_circular_dependency_detected() -> None:
    """Test circular dependency detection."""
    graph = DependencyGraph()
    graph.add_table("A", ["B"])
    graph.add_table("B", ["A"])

    ordered, cycle = graph.get_processing_order()

    assert ordered == [], "Should return empty list on cycle"
    assert cycle is not None, "Should detect cycle"
    assert set(cycle) == {"A", "B"}, "Cycle should contain both tables"


def test_complex_graph() -> None:
    """Test multi-level dependency graph."""
    graph = DependencyGraph()
    graph.add_table("users", [])
    graph.add_table("posts", ["users"])
    graph.add_table("comments", ["posts", "users"])
    graph.add_table("likes", ["comments", "users"])

    ordered, cycle = graph.get_processing_order()

    assert cycle is None, "Should not detect cycle"
    assert len(ordered) == 4, "Should include all four tables"
    # Verify dependency constraints
    users_idx = ordered.index("users")
    posts_idx = ordered.index("posts")
    comments_idx = ordered.index("comments")
    likes_idx = ordered.index("likes")

    assert users_idx < posts_idx, "users must come before posts"
    assert posts_idx < comments_idx, "posts must come before comments"
    assert users_idx < comments_idx, "users must come before comments"
    assert comments_idx < likes_idx, "comments must come before likes"
    assert users_idx < likes_idx, "users must come before likes"


def test_empty_graph() -> None:
    """Test empty graph returns empty order."""
    graph = DependencyGraph()

    ordered, cycle = graph.get_processing_order()

    assert ordered == [], "Empty graph should return empty list"
    assert cycle is None, "Empty graph should not have cycle"


def test_single_table_no_dependencies() -> None:
    """Test single independent table."""
    graph = DependencyGraph()
    graph.add_table("standalone", [])

    ordered, cycle = graph.get_processing_order()

    assert cycle is None, "Should not detect cycle"
    assert ordered == ["standalone"], "Should include single table"


def test_multiple_roots() -> None:
    """Test graph with multiple independent root tables."""
    graph = DependencyGraph()
    graph.add_table("A", [])
    graph.add_table("B", [])
    graph.add_table("C", ["A"])
    graph.add_table("D", ["B"])

    ordered, cycle = graph.get_processing_order()

    assert cycle is None, "Should not detect cycle"
    assert len(ordered) == 4, "Should include all four tables"
    # A and B must come before C and D respectively
    a_idx = ordered.index("A")
    b_idx = ordered.index("B")
    c_idx = ordered.index("C")
    d_idx = ordered.index("D")

    assert a_idx < c_idx, "A must come before C"
    assert b_idx < d_idx, "B must come before D"
    # A and B can be in any order relative to each other
    assert set(ordered[:2]) == {"A", "B"}, "A and B should be roots"
