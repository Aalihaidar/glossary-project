import glossary_pb2 as _glossary_pb2
import graph_pb2 as _graph_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import (
    ClassVar as _ClassVar,
    Iterable as _Iterable,
    Mapping as _Mapping,
    Optional as _Optional,
    Union as _Union,
)

DESCRIPTOR: _descriptor.FileDescriptor

class Node(_message.Message):
    __slots__ = ("id", "name", "definition")
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    DEFINITION_FIELD_NUMBER: _ClassVar[int]
    id: str
    name: str
    definition: str
    def __init__(
        self,
        id: _Optional[str] = ...,
        name: _Optional[str] = ...,
        definition: _Optional[str] = ...,
    ) -> None: ...

class Edge(_message.Message):
    __slots__ = ("from_id", "to_id", "label")
    FROM_ID_FIELD_NUMBER: _ClassVar[int]
    TO_ID_FIELD_NUMBER: _ClassVar[int]
    LABEL_FIELD_NUMBER: _ClassVar[int]
    from_id: str
    to_id: str
    label: str
    def __init__(
        self,
        from_id: _Optional[str] = ...,
        to_id: _Optional[str] = ...,
        label: _Optional[str] = ...,
    ) -> None: ...

class GetMindMapForTermRequest(_message.Message):
    __slots__ = ("term_id",)
    TERM_ID_FIELD_NUMBER: _ClassVar[int]
    term_id: str
    def __init__(self, term_id: _Optional[str] = ...) -> None: ...

class GetMindMapForTermResponse(_message.Message):
    __slots__ = ("nodes", "edges")
    NODES_FIELD_NUMBER: _ClassVar[int]
    EDGES_FIELD_NUMBER: _ClassVar[int]
    nodes: _containers.RepeatedCompositeFieldContainer[Node]
    edges: _containers.RepeatedCompositeFieldContainer[Edge]
    def __init__(
        self,
        nodes: _Optional[_Iterable[_Union[Node, _Mapping]]] = ...,
        edges: _Optional[_Iterable[_Union[Edge, _Mapping]]] = ...,
    ) -> None: ...

class AddRelationshipRequest(_message.Message):
    __slots__ = ("from_term_id", "to_term_id", "type")
    FROM_TERM_ID_FIELD_NUMBER: _ClassVar[int]
    TO_TERM_ID_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    from_term_id: str
    to_term_id: str
    type: _graph_pb2.RelationshipType
    def __init__(
        self,
        from_term_id: _Optional[str] = ...,
        to_term_id: _Optional[str] = ...,
        type: _Optional[_Union[_graph_pb2.RelationshipType, str]] = ...,
    ) -> None: ...

class AddRelationshipResponse(_message.Message):
    __slots__ = ("success",)
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    success: bool
    def __init__(self, success: bool = ...) -> None: ...
