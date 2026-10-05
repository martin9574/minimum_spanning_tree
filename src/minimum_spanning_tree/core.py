"""Core implementation of Kruskal's algorithm with a disjoint-set (union-find) structure.

Design decisions, stated plainly so the tests do not invent their own requirements:

* The graph is undirected. Every added edge is stored once, as an ordered
  ``(u, v, weight)`` triple with ``u < v``. This canonical form keeps the
  ``iter_edges`` output stable regardless of the order in which a caller
  adds the two directions of the same edge.
* Vertex identifiers are arbitrary hashable, comparable Python objects.
  Comparability is required solely so we can canonicalise endpoints as
  ``(min(a,b), max(a,b))``. Strings, ints, and tuples of ints all work.
* Weights are numbers. They are never compared with ``==`` inside this
  library; Kruskal only needs total ordering among weights, which Python
  provides for ``int`` and ``float``. Ties are broken deterministically by
  endpoint tuple, so two different runs over the same graph yield the same
  tree.
* Self-loops are rejected at add time: a self-loop can never belong to a
  spanning tree, and silently dropping it would hide a likely caller bug.
* Parallel edges are permitted; the algorithm picks whichever is lighter
  (or, on a tie, whichever sorts first by endpoints). Duplicate edges with
  equal weight and equal canonical endpoints are de-duplicated so the tree
  never contains two copies of the same edge.
* If the graph has fewer than one vertex, the MST is empty. If the graph is
  disconnected, we raise ``MSTError`` — there is no spanning tree. A graph
  with one vertex and no edges has a valid (empty) spanning tree.
* The returned tree is a list of ``(u, v, weight)`` triples with ``u < v``.
  An empty list means the graph was a single isolated vertex (or, trivially,
  empty); the caller distinguishes these by vertex count.
"""

from __future__ import annotations

from typing import Hashable, Iterator, List, Tuple

Edge = Tuple[object, object, float]


class MSTError(Exception):
    """Raised when no spanning tree exists for the given graph."""


class DisjointSet:
    """Union-by-rank disjoint-set with path compression.

    We use rank rather than size because rank updates are simpler and the
    worst-case tree height is the same asymptotically. Path compression is
    applied on every ``find``. This is the textbook union-find that makes
    Kruskal's algorithm run in nearly-linear total time.
    """

    __slots__ = ("_parent", "_rank")

    def __init__(self) -> None:
        self._parent: dict = {}
        self._rank: dict = {}

    def add(self, x: Hashable) -> None:
        if x not in self._parent:
            self._parent[x] = x
            self._rank[x] = 0

    def find(self, x: Hashable) -> Hashable:
        # Iterative path compression to avoid recursion limits on deep,
        # pathological trees built up by a long chain of unions.
        root = x
        while self._parent[root] != root:
            root = self._parent[root]
        cursor = x
        while self._parent[cursor] != root:
            self._parent[cursor], cursor = root, self._parent[cursor]
        return root

    def union(self, x: Hashable, y: Hashable) -> bool:
        """Merge the sets containing ``x`` and ``y``.

        Returns ``True`` if two distinct sets were merged, ``False`` if they
        were already the same set (which is exactly the signal Kruskal's
        algorithm uses to reject an edge that would form a cycle).
        """
        rx, ry = self.find(x), self.find(y)
        if rx == ry:
            return False
        # Attach the shorter tree under the taller one. Rank only increases
        # when two equally-ranked trees merge.
        if self._rank[rx] < self._rank[ry]:
            rx, ry = ry, rx
        self._parent[ry] = rx
        if self._rank[rx] == self._rank[ry]:
            self._rank[rx] += 1
        return True


class Graph:
    """An undirected, edge-weighted graph.

    Internally edges live in a set keyed by canonical ``(min, max, weight)``
    tuples. This gives O(1) duplicate detection and a stable iteration order
    when we sort at query time. The cost is memory linear in the edge count,
    which is the only cost Kruskal already pays, so no new asymptotic penalty.
    """

    __slots__ = ("_vertices", "_edges")

    def __init__(self) -> None:
        self._vertices: set = set()
        self._edges: set = set()

    def add_vertex(self, v: Hashable) -> None:
        self._vertices.add(v)

    def add_edge(self, u: Hashable, v: Hashable, weight: float) -> None:
        """Add an undirected edge between ``u`` and ``v`` with the given weight.

        Raises ``ValueError`` on a self-loop. Adding the same edge twice
        (in either direction, with the same weight) is a no-op rather than a
        duplicate. Parallel edges with different weights are both kept.
        """
        if u == v:
            raise ValueError(f"self-loop not allowed: {u!r} == {v!r}")
        a, b = (u, v) if u < v else (v, u)
        self._vertices.add(a)
        self._vertices.add(b)
        self._edges.add((a, b, weight))

    @property
    def vertices(self) -> set:
        return set(self._vertices)

    def iter_edges(self) -> Iterator[Edge]:
        """Yield edges sorted by weight, then by endpoints.

        Sorting here, once, at query time keeps construction cheap and
        guarantees Kruskal sees a deterministic edge order even when two
        edges share a weight.
        """
        return iter(sorted(self._edges, key=lambda e: (e[2], e[0], e[1])))

    def edge_count(self) -> int:
        return len(self._edges)


def minimum_spanning_tree(graph: Graph) -> List[Edge]:
    """Return the minimum-weight spanning tree of ``graph`` as a list of edges.

    Raises ``MSTError`` if ``graph`` is disconnected, since no spanning tree
    exists in that case. A graph with zero or one vertex yields an empty list.
    """
    vertices = graph.vertices
    if len(vertices) <= 1:
        return []

    dsu = DisjointSet()
    for v in vertices:
        dsu.add(v)

    tree: List[Edge] = []
    needed = len(vertices) - 1
    for u, v, w in graph.iter_edges():
        if dsu.union(u, v):
            tree.append((u, v, w))
            if len(tree) == needed:
                break

    if len(tree) != needed:
        # Fewer edges than ``needed`` means the graph is in multiple
        # components; the union operations simply ran out before connecting
        # everyone.
        raise MSTError(
            f"graph is disconnected: spanning tree has {len(tree)} edges "
            f"but {needed} are required for {len(vertices)} vertices"
        )
    return tree
