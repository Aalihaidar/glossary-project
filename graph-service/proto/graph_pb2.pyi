from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
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

class RelationshipType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    RELATED_TO: _ClassVar[RelationshipType]
    SYNONYM: _ClassVar[RelationshipType]
    ANTONYM: _ClassVar[RelationshipType]
    IS_A: _ClassVar[RelationshipType]
    CONTAINS: _ClassVar[RelationshipType]

RELATED_TO: RelationshipType
SYNONYM: RelationshipType
ANTONYM: RelationshipType
IS_A: RelationshipType
CONTAINS: RelationshipType

class Relationship(_message.Message):
    __slots__ = ("from_term_id", "to_term_id", "type")
    FROM_TERM_ID_FIELD_NUMBER: _ClassVar[int]
    TO_TERM_ID_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    from_term_id: str
    to_term_id: str
    type: RelationshipType
    def __init__(
        self,
        from_term_id: _Optional[str] = ...,
        to_term_id: _Optional[str] = ...,
        type: _Optional[_Union[RelationshipType, str]] = ...,
    ) -> None: ...

class AddRelationshipRequest(_message.Message):
    __slots__ = ("from_term_id", "to_term_id", "type")
    FROM_TERM_ID_FIELD_NUMBER: _ClassVar[int]
    TO_TERM_ID_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    from_term_id: str
    to_term_id: str
    type: RelationshipType
    def __init__(
        self,
        from_term_id: _Optional[str] = ...,
        to_term_id: _Optional[str] = ...,
        type: _Optional[_Union[RelationshipType, str]] = ...,
    ) -> None: ...

class AddRelationshipResponse(_message.Message):
    __slots__ = ("message",)
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    message: str
    def __init__(self, message: _Optional[str] = ...) -> None: ...

class GetRelationshipsForTermRequest(_message.Message):
    __slots__ = ("term_id",)
    TERM_ID_FIELD_NUMBER: _ClassVar[int]
    term_id: str
    def __init__(self, term_id: _Optional[str] = ...) -> None: ...

class GetRelationshipsForTermResponse(_message.Message):
    __slots__ = ("relationships",)
    RELATIONSHIPS_FIELD_NUMBER: _ClassVar[int]
    relationships: _containers.RepeatedCompositeFieldContainer[Relationship]
    def __init__(
        self, relationships: _Optional[_Iterable[_Union[Relationship, _Mapping]]] = ...
    ) -> None: ...

class DeleteRelationshipRequest(_message.Message):
    __slots__ = ("from_term_id", "to_term_id")
    FROM_TERM_ID_FIELD_NUMBER: _ClassVar[int]
    TO_TERM_ID_FIELD_NUMBER: _ClassVar[int]
    from_term_id: str
    to_term_id: str
    def __init__(
        self, from_term_id: _Optional[str] = ..., to_term_id: _Optional[str] = ...
    ) -> None: ...

class DeleteRelationshipResponse(_message.Message):
    __slots__ = ("message",)
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    message: str
    def __init__(self, message: _Optional[str] = ...) -> None: ...
