# minimum_spanning_tree

Computes a minimum-weight spanning tree of an undirected, edge-weighted graph using Kruskal's algorithm with a union-by-rank, path-compressed disjoint set. Standard library only, no third-party dependencies.

## Usage

```python
from minimum_spanning_tree import Graph, minimum_spanning_tree, MSTError

g = Graph()
g.add_edge("a", "b", 1.0)
g.add_edge("b", "c", 2.0)
g.add_edge("a", "c", 3.0)

try:
    tree = minimum_spanning_tree(g)
except MSTError:
    tree = None  # graph is disconnected

# tree == [("a", "b", 1.0), ("b", "c", 2.0)]
```

The exported names are: `Graph`, `minimum_spanning_tree`, `DisjointSet`, and `MSTError`.

## Why this exists

I wanted a small, dependency-free MST routine I could drop into a project that already pins its dependency set tightly. Kruskal's algorithm plus union-find is the simplest correct choice for sparse graphs; the alternative, Prim's algorithm, is better for dense graphs but needs a priority queue, which in the standard library means `heapq` plus index bookkeeping that is easy to get wrong. The trade-off here is simplicity and zero dependencies over asymptotic optimality on dense inputs.

## Edge cases you will hit

- **Self-loops** are rejected at `add_edge` time with `ValueError`. A self-loop can never be in a spanning tree, and silently ignoring it would mask caller bugs.
- **Disconnected graphs** raise `MSTError` from `minimum_spanning_tree`. There is no spanning tree, and returning a partial forest would mislead callers who asked for a tree.
- **A single isolated vertex** (or an empty graph) returns an empty list, not an error. A tree over one vertex has zero edges, which is valid.
- **Parallel edges** with different weights are both kept; Kruskal picks the cheaper one. Parallel edges with the same weight are de-duplicated so the tree never contains two copies of the same edge.
- **Ties in weight** are broken by endpoint tuple, so two runs over the same graph always produce the same tree. If you need a different tie-break, sort the edges yourself before calling a Kruskal implementation that accepts a pre-sorted list — this library does not expose that hook.

Run the tests with:

```
PYTHONPATH=src python -m unittest discover -s tests
```

## Design notes

The window stores values eagerly rather than keeping running aggregates. Running
sums drift with floating point over long streams, and recomputing from a small
buffer is cheap enough that the drift is not worth the speed.

## Limitations

Values are coerced to floats, so very large integers lose precision. If you need
exact integer aggregates over a window, this is the wrong tool.

