"""MergedKG and MergeQC classes."""
from pandas.core.frame import DataFrame


class MergedKG:

    """Class for merged knowledge graph."""

    def __init__(
        self,
        nodes: DataFrame,
        edges: DataFrame,
    ):
        """Initialize MergedKG object."""
        self.nodes = nodes
        self.edges = edges


class MergeQC:

    """Class for merge quality control."""

    def __init__(self, duplicate_nodes: DataFrame, duplicate_edges: DataFrame, dangling_edges: DataFrame):
        """Initialize MergeQC object."""
        self.duplicate_nodes = duplicate_nodes
        self.duplicate_edges = duplicate_edges
        self.dangling_edges = dangling_edges
