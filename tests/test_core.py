import unittest

from minimum_spanning_tree import Graph, minimum_spanning_tree, DisjointSet, MSTError


class TestDisjointSet(unittest.TestCase):
    def test_union_returns_true_on_merge(self):
        ds = DisjointSet()
        ds.add("a")
        ds.add("b")
        self.assertTrue(ds.union("a", "b"))

    def test_union_returns_false_within_same_set(self):
        ds = DisjointSet()
        ds.add("a")
        ds.add("b")
        ds.union("a", "b")
        self.assertFalse(ds.union("a", "b"))

    def test_find_after_transitive_unions(self):
        ds = DisjointSet()
        for v in range(10):
            ds.add(v)
        for i in range(9):
            ds.union(i, i + 1)
        root = ds.find(0)
        for i in range(10):
            self.assertEqual(ds.find(i), root)

    def test_add_is_idempotent(self):
        ds = DisjointSet()
        ds.add("x")
        ds.add("x")
        self.assertEqual(ds.find("x"), "x")


class TestGraph(unittest.TestCase):
    def test_self_loop_rejected(self):
        g = Graph()
        with self.assertRaises(ValueError):
            g.add_edge("a", "a", 1.0)

    def test_duplicate_edge_collapsed(self):
        g = Graph()
        g.add_edge("a", "b", 2.0)
        g.add_edge("b", "a", 2.0)  # same endpoints, same weight
        self.assertEqual(g.edge_count(), 1)

    def test_parallel_edges_with_different_weights_kept(self):
        g = Graph()
        g.add_edge("a", "b", 2.0)
        g.add_edge("a", "b", 1.0)
        self.assertEqual(g.edge_count(), 2)

    def test_iter_edges_sorted_by_weight_then_endpoints(self):
        g = Graph()
        g.add_edge("b", "c", 1.0)
        g.add_edge("a", "b", 1.0)
        g.add_edge("a", "c", 0.5)
        edges = list(g.iter_edges())
        self.assertEqual(edges[0], ("a", "c", 0.5))
        self.assertEqual(edges[1], ("a", "b", 1.0))
        self.assertEqual(edges[2], ("b", "c", 1.0))

    def test_vertex_set_independent_mutation(self):
        g = Graph()
        g.add_edge("a", "b", 1.0)
        vs = g.vertices
        vs.add("z")
        self.assertNotIn("z", g.vertices)


class TestKruskal(unittest.TestCase):
    def test_triangle_picks_two_cheapest(self):
        g = Graph()
        g.add_edge("a", "b", 1.0)
        g.add_edge("b", "c", 2.0)
        g.add_edge("a", "c", 3.0)
        tree = minimum_spanning_tree(g)
        self.assertEqual(tree, [("a", "b", 1.0), ("b", "c", 2.0)])

    def test_single_vertex_empty_tree(self):
        g = Graph()
        g.add_vertex("a")
        self.assertEqual(minimum_spanning_tree(g), [])

    def test_empty_graph_empty_tree(self):
        g = Graph()
        self.assertEqual(minimum_spanning_tree(g), [])

    def test_disconnected_graph_raises(self):
        g = Graph()
        g.add_edge("a", "b", 1.0)
        g.add_edge("c", "d", 1.0)
        with self.assertRaises(MSTError):
            minimum_spanning_tree(g)

    def test_parallel_edges_cheaper_one_chosen(self):
        g = Graph()
        g.add_edge("a", "b", 5.0)
        g.add_edge("a", "b", 1.0)
        g.add_edge("b", "c", 2.0)
        g.add_edge("a", "c", 3.0)
        tree = minimum_spanning_tree(g)
        weights = sorted(w for _, _, w in tree)
        self.assertEqual(weights, [1.0, 2.0])
        self.assertEqual(len(tree), 2)

    def test_tie_breaking_is_deterministic(self):
        # Two edges of equal weight; the one with lexicographically smaller
        # endpoint pair must come first, deterministically.
        g = Graph()
        g.add_edge("a", "c", 1.0)
        g.add_edge("a", "b", 1.0)
        g.add_edge("b", "c", 2.0)
        tree = minimum_spanning_tree(g)
        self.assertEqual(tree[0], ("a", "b", 1.0))
        self.assertEqual(tree[1], ("a", "c", 1.0))

    def test_larger_connected_graph(self):
        # Textbook four-vertex example.
        g = Graph()
        g.add_edge("a", "b", 1.0)
        g.add_edge("a", "d", 3.0)
        g.add_edge("b", "d", 2.0)
        g.add_edge("b", "c", 4.0)
        g.add_edge("c", "d", 5.0)
        tree = minimum_spanning_tree(g)
        total = sum(w for _, _, w in tree)
        self.assertEqual(len(tree), 3)
        self.assertEqual(total, 7.0)

    def test_endpoints_canonicalised_in_output(self):
        g = Graph()
        g.add_edge("z", "a", 1.0)  # added in "reverse" order
        g.add_vertex("z")
        g.add_vertex("a")
        tree = minimum_spanning_tree(g)
        self.assertEqual(tree, [("a", "z", 1.0)])

    def test_integer_weights(self):
        g = Graph()
        g.add_edge(0, 1, 3)
        g.add_edge(1, 2, 1)
        g.add_edge(0, 2, 2)
        tree = minimum_spanning_tree(g)
        self.assertEqual(tree, [(1, 2, 1), (0, 2, 2)])


if __name__ == "__main__":
    unittest.main()
