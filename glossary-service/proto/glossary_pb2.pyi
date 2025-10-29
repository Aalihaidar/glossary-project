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

class Term(_message.Message):
    __slots__ = ("id", "name", "definition", "source_url")
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    DEFINITION_FIELD_NUMBER: _ClassVar[int]
    SOURCE_URL_FIELD_NUMBER: _ClassVar[int]
    id: str
    name: str
    definition: str
    source_url: str
    def __init__(
        self,
        id: _Optional[str] = ...,
        name: _Optional[str] = ...,
        definition: _Optional[str] = ...,
        source_url: _Optional[str] = ...,
    ) -> None: ...

class AddTermRequest(_message.Message):
    __slots__ = ("name", "definition", "source_url")
    NAME_FIELD_NUMBER: _ClassVar[int]
    DEFINITION_FIELD_NUMBER: _ClassVar[int]
    SOURCE_URL_FIELD_NUMBER: _ClassVar[int]
    name: str
    definition: str
    source_url: str
    def __init__(
        self,
        name: _Optional[str] = ...,
        definition: _Optional[str] = ...,
        source_url: _Optional[str] = ...,
    ) -> None: ...

class UpdateTermRequest(_message.Message):
    __slots__ = ("id", "name", "definition", "source_url")
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    DEFINITION_FIELD_NUMBER: _ClassVar[int]
    SOURCE_URL_FIELD_NUMBER: _ClassVar[int]
    id: str
    name: str
    definition: str
    source_url: str
    def __init__(
        self,
        id: _Optional[str] = ...,
        name: _Optional[str] = ...,
        definition: _Optional[str] = ...,
        source_url: _Optional[str] = ...,
    ) -> None: ...

class GetTermRequest(_message.Message):
    __slots__ = ("id",)
    ID_FIELD_NUMBER: _ClassVar[int]
    id: str
    def __init__(self, id: _Optional[str] = ...) -> None: ...

class GetAllTermsRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class GetAllTermsResponse(_message.Message):
    __slots__ = ("terms",)
    TERMS_FIELD_NUMBER: _ClassVar[int]
    terms: _containers.RepeatedCompositeFieldContainer[Term]
    def __init__(
        self, terms: _Optional[_Iterable[_Union[Term, _Mapping]]] = ...
    ) -> None: ...

class DeleteTermRequest(_message.Message):
    __slots__ = ("id",)
    ID_FIELD_NUMBER: _ClassVar[int]
    id: str
    def __init__(self, id: _Optional[str] = ...) -> None: ...

class DeleteTermResponse(_message.Message):
    __slots__ = ("success",)
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    success: bool
    def __init__(self, success: bool = ...) -> None: ...
