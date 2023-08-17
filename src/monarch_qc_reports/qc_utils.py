"""Utility functions for qc reports."""

from typing import Dict, List, Union

import pandas as pd

# from grape import Graph  # type: ignore
from monarch_qc_reports.model.merged_kg import MergedKG, MergeQC


def create_edge_report(edges_grouped_by, edges_grouped_by_values, unique_id_from_nodes) -> Dict:
    """
    Create a report for a given edge type.

    Params:
        edges_grouped_by: the name of the edge type
        edges_grouped_by_values: the values for the edge type
        unique_id_from_nodes: the unique ids from the nodes

    Returns
    -------
        A Dict with the edge report
    """
    edge_object = {
        "name": edges_grouped_by,
        "namespaces": col_to_yaml(
            get_namespace(
                pd.concat([edges_grouped_by_values["subject"], edges_grouped_by_values["object"]])
            ).drop_duplicates()
        ),
        "categories": col_to_yaml(edges_grouped_by_values["category"]),
        "total_number": edges_grouped_by_values["id"].size,
        "missing_old": len(
            get_missing_old(
                [edges_grouped_by_values["subject"], edges_grouped_by_values["object"]], unique_id_from_nodes
            )
        ),
        "missing": len(get_missing(edges_grouped_by_values, ["subject", "object"], unique_id_from_nodes)),
        "predicates": [],
        "node_types": [],
    }

    return edge_object


def get_missing(edges: pd.DataFrame, cols: List[str], ids: pd.Series) -> pd.Series:
    """
    Get missing ids from a dataframe.

    Params:
        edges (pd.DataFrame): the dataframe to check
        cols (List[str]): the columns to check
        ids (pd.Series): the unique ids from the nodes

    Returns
    -------
        A pd.Series of missing ids
    """
    # Have to convert the dtype of the series back to the same dtype after the melt
    return get_difference(edges.melt(value_vars=cols)["value"].convert_dtypes(), ids)


def create_predicate_report(
    edges_grouped_by_values: pd.DataFrame, node_ids: pd.Series, data_type: type = dict, group_by: str = "predicate"
) -> Union[List[Dict], Dict]:
    """
    Create a report for a given predicate.

    Params:
        edges_grouped_by_values (pd.DataFrame): the values for the predicate
        node_ids (pd.Series): unique node ids
        data_type (type): the type of data object to return
        group_by (str): the name of the column to group by

    Returns
    -------
        A List or Dict with the predicate report
    """
    predicates = ReportContainer(data_type, key_name="uri")
    predicate_group = edges_grouped_by_values.groupby([group_by])[["id", "object", "subject", "category"]]
    for predicate, predicate_values in predicate_group:
        predicate_object = {
            "uri": predicate,
            "total_number": predicate_values["id"].size,
            "missing_subjects": len(set(predicate_values["subject"]) - set(node_ids)),
            "missing_objects": len(set(predicate_values["object"]) - set(node_ids)),
            "missing_subject_namespaces": col_to_yaml(
                get_namespace(get_difference(predicate_values["subject"], node_ids))
            ),
            "missing_object_namespaces": col_to_yaml(
                get_namespace(get_difference(predicate_values["object"], node_ids))
            ),
        }
        predicates.add(predicate_object)
    return predicates.data


def create_edges_report(
    edges: pd.DataFrame, nodes: pd.DataFrame, data_type: type = dict, group_by: str = "provided_by"
) -> Union[List[Dict], Dict]:
    """
    Create a report for a given edge.

    Params:
        edges (pd.DataFrame): dataframe of edges
        nodes (pd.DataFrame): dataframe of nodes
        data_type (type): type of data object to return
        group_by (str): column to group by

    Returns
    -------
        A List or Dict with the edge report
    """
    edges_report = ReportContainer(data_type)
    if len(edges) == 0:
        return edges_report.data

    edges_group = edges.groupby([group_by])[["id", "object", "subject", "predicate", "category"]]
    for edge_group_name, edge_group_values in edges_group:
        # edge_object = create_edge_report(edges_grouped_by, edge_group_values, nodes["id"])
        missing = len(get_missing(edge_group_values, ["subject", "object"], nodes["id"]))
        edge_object = {
            "name": edge_group_name,
            # "namespaces": col_to_yaml(get_namespace(
            #     pd.concat([edge_group_values['subject'], edge_group_values['object']])
            # )),
            "namespaces": col_to_yaml(get_namespace(edge_group_values[["subject", "object"]].stack())),
            "categories": col_to_yaml(edge_group_values["category"]),
            "total_number": edge_group_values["id"].size,
            "missing_old": len(
                get_missing_old([edge_group_values["subject"], edge_group_values["object"]], nodes["id"])
            ),
            "missing": missing,
            "predicates": create_predicate_report(edge_group_values, nodes["id"], data_type),
            "node_types": create_nodes_report(nodes, edge_group_values, data_type, group_by),
        }
        if missing > 0:
            missing_subject_namespaces = get_namespace(get_missing(edge_group_values, ["subject"], nodes["id"]))
            edge_object["missing_subject_namespaces"] = missing_subject_namespaces
            missing_object_namespaces = get_namespace(get_missing(edge_group_values, ["object"], nodes["id"]))
            edge_object["missing_object_namespaces"] = missing_object_namespaces
        edges_report.add(edge_object)
    return edges_report.data


def get_namespace(col: pd.Series) -> pd.Series:
    """
    Get the namespace from a column.

    Params:
        col (pd.Series): column to get namespace from

    Returns
    -------
        series of namespaces from the provided column
    """
    return col if len(col) == 0 else col.str.split(":").str[0]


def col_to_yaml(col: pd.Series) -> List[str]:
    """
    Convert a column from pandas to data for yaml report.

    Params:
        col (pd.Series): column to convert

    Returns
    -------
        List of values from the column
    """
    # This probably should have a better name
    # Convert a column from pandas to data for yaml report
    return col.drop_duplicates().sort_values().tolist()


def get_missing_old(cols: List[pd.Series], ids: pd.Series) -> List[str]:
    """
    Get the missing ids from a list of columns.

    Params:
        cols (List[pd.Series]): list of columns to get missing ids from
        ids (pd.Series): ids to check against

    Returns
    -------
        List of missing ids
    """
    return get_difference(pd.concat(cols).drop_duplicates().sort_values().tolist(), ids.tolist())


class ReportContainer:

    """
    Container for report data.

    This class provides a container for report data that can be added and retrieved using a unique identifier.
    The data can be stored in a dictionary or a list. When data is added to the container, it is checked to ensure
    that the unique identifier (specified by `key_name`) is present in the dictionary, and not already in use.

    Params:
        data_type (type, optional): Type of data container to use. Supported values are `list` and `dict`.
            Defaults to `dict`.
        key_name (str, optional): Name of the key to use for the unique identifier.

    Raises
    ------
        ValueError: If `data_type` is not a `list` or `dict`.
    """

    def __init__(self, data_type: type = dict, key_name: str = "name"):
        """
        Initialize a new instance of the `ReportContainer` class.

        Params:
            data_type (type, optional): Type of data container to use. Supported values are `list` and `dict`.
                Defaults to `dict`.
            key_name (str, optional): Name of the key to use for the unique identifier.

        Raises
        ------
            ValueError: If `data_type` is not a `list` or `dict`.
        """
        self.data_type = data_type
        self.key_name = key_name
        match data_type:
            case type() if data_type in [list, dict]:
                self.data = data_type()
            case _:
                message = (
                    "ReportContainer: data_type: type: "
                    + str(type(data_type))
                    + " value: '"
                    + str(data_type)
                    + "' not allowed, supports list and dict."
                )
                raise ValueError(message)

    def add(self, addend: dict, key_name: str = None):
        """
        Add a dictionary to the container.

        Params:
            addend (dict): dictionary to add to the container
            key_name (str, optional): Name of the key to use for the unique identifier.

        Raises
        ------
            KeyError: If the key in `key_name` is not present in the dictionary or already in the container.
            RuntimeError: If the container is not a `list` or `dict`.
        """
        match self.data:
            case list():
                self.data.append(addend)
            case dict():
                key = key_name if key_name is not None else self.key_name
                if type(addend) is dict and key in addend.keys():
                    if key in self.data.keys():
                        message = "ReportContainer: key: '" + key + "' already added to data."
                        raise KeyError(message)
                    else:
                        self.data[addend.get(key)] = addend
                else:
                    message = "ReportContainer: key: '" + key + "' missing from dict to add."
                    raise KeyError(message)
            case _:
                message = "ReportContainer: attempting to add to invalid data type: " + str(type(self.data))
                raise RuntimeError(message)


def create_nodes_report(
    nodes: pd.DataFrame, edges: pd.DataFrame = None, data_type: type = dict, group_by: str = "provided_by"
) -> Union[List[Dict], Dict]:
    """
    Create a report for nodes.

    Params:
        nodes (pd.DataFrame): nodes to create report for
        edges (pd.DataFrame, optional): edges to create report for. Defaults to None.
        data_type (type, optional): Type of data container to use. Supported values are `list` and `dict`.
            Defaults to `dict`.
        group_by (str, optional): column to group nodes by. Defaults to "provided_by".

    Returns
    -------
        List or Dict of nodes report
    """
    node_report = ReportContainer(data_type)
    if len(nodes) == 0:
        return node_report.data

    if edges is not None:
        subject_nodes = list(get_intersection(edges["subject"], nodes["id"]))
        object_nodes = list(get_intersection(edges["object"], nodes["id"]))

        edge_nodes = subject_nodes + object_nodes
        nodes_df = nodes[nodes["id"].isin(edge_nodes)]
    else:
        nodes_df = nodes

    node_grouping_fields = get_intersection(list(nodes_df.columns), ["id", "category", "in_taxon"])
    nodes_group = nodes_df.groupby([group_by])[node_grouping_fields]
    for nodes_group_name, nodes_group_values in nodes_group:
        node_object = {
            "name": nodes_group_name,
            "namespaces": col_to_yaml(get_namespace(nodes_group_values["id"])),
            "categories": col_to_yaml(nodes_group_values["category"]),
            "total_number": nodes_group_values["id"].size,
        }
        if edges is not None:
            missing_subjects = get_difference(nodes_group_values["id"], edges["subject"])
            missing_objects = get_difference(nodes_group_values["id"], edges["object"])

            missing_nodes = missing_subjects.size + missing_objects.size
            node_object["missing"] = missing_nodes
            if missing_nodes > 0:
                node_object["missing_objects"] = missing_objects.size
                node_object["missing_subjects"] = missing_subjects.size

        if "in_taxon" in nodes.columns:
            node_object["taxon"] = col_to_yaml(nodes_group_values["in_taxon"])
        node_report.add(node_object)
    return node_report.data


def cols_fill_na(df: pd.DataFrame, names_values: dict) -> pd.DataFrame:
    """
    Fill NA values in columns of a dataframe.

    Params:
        df (pd.DataFrame): dataframe to fill NA values in
        names_values (dict): dictionary of column names and values to fill NA with in the columns

    Returns
    -------
        pd.DataFrame with NA values replaced with the specified values
    """
    for col_name, fill_value in names_values.items():
        if col_name in df.columns:
            df[col_name] = df[col_name].fillna(fill_value)
    return df


def get_intersection(a: Union[List, pd.Series], b: Union[List, pd.Series]) -> Union[List, pd.Series]:
    """
    Get the intersection of two lists or pandas.Series.

    Params:
        a (Union[List, pd.Series]): first list or pandas.Series
        b (Union[List, pd.Series]): second list or pandas.Series

    Returns
    -------
        Union[List, pd.Series]: intersection of the two lists or pandas.Series
    """
    if type(a) != type(b):
        raise ValueError("get_intersection: arguments must have the same type")
    elif not (type(a) is list or type(a) is pd.Series):
        raise ValueError("get_intersection: arguments must be of type list or pandas.Series")

    s = sorted(list(set(a) & set(b)))
    return s if type(a) is list else pd.Series(s, dtype=a.dtype, name=a.name)


def get_difference(a: Union[List, pd.Series], b: Union[List, pd.Series]) -> Union[List, pd.Series]:
    """
    Get the difference of two lists or pandas.Series.

    Params:
        a (Union[List, pd.Series]): first list or pandas.Series
        b (Union[List, pd.Series]): second list or pandas.Series

    Returns
    -------
        Union[List, pd.Series]: difference of the two lists or pandas.Series
    """
    if type(a) != type(b):
        raise ValueError("get_difference: arguments must have the same type")
    elif not (type(a) is list or type(a) is pd.Series):
        raise ValueError("get_difference: arguments must be of type list or pandas.Series")

    s = sorted(list(set(a) - set(b)))
    return s if type(a) is list else pd.Series(s, dtype=a.dtype, name=a.name)


def create_qc_report(kg: MergedKG, qc: MergeQC, data_type: type = dict, group_by: str = "provided_by") -> Dict:
    """
    interface for generating qc report from merged kg.

    Params:
        kg (MergedKG): merged kg to generate qc report for
        qc (MergeQC): qc data to generate qc report for
        data_type (type, optional): Type of data container to use. Supported values are `list` and `dict`.
            Defaults to `dict`.
        group_by (str, optional): column to group nodes by. Defaults to "provided_by".

    Returns
    -------
        Dict of qc report
    """
    nodes = cols_fill_na(kg.nodes, {"in_taxon": "missing taxon", "category": "missing category"})
    ingest_collection = {
        "nodes": create_nodes_report(nodes, data_type=data_type, group_by=group_by),
        "duplicate_nodes": create_nodes_report(qc.duplicate_nodes, data_type=data_type, group_by=group_by),
        "edges": create_edges_report(kg.edges, nodes, data_type, group_by),
        "dangling_edges": create_edges_report(qc.dangling_edges, nodes, data_type, group_by),
        "duplicate_edges": create_edges_report(qc.duplicate_edges, nodes, data_type, group_by),
    }

    return ingest_collection
