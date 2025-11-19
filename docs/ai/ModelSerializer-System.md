# ModelSerializer System

> **Relevant source files**
> * [fastapp/filters/filters.py](/fastapp/filters/filters.py)
> * [fastapp/filters/filterset.py](/fastapp/filters/filterset.py)
> * [fastapp/serializers/creator.py](/fastapp/serializers/creator.py)
> * [fastapp/serializers/fields/__init__.py](/fastapp/serializers/fields/__init__.py)
> * [fastapp/serializers/model.py](/fastapp/serializers/model.py)

The ModelSerializer system provides automatic Pydantic model generation from Tortoise ORM models, enabling seamless serialization, validation, and data conversion between database models and API representations. This system is the core bridge between QingKongFramework's data layer and API responses, automatically handling complex relationships, field validation, and database operations.

For information about query parameter filtering with Pydantic validation, see [FilterSet System](FilterSet-System.md). For database model extensions and QuerySet functionality, see [BaseModel Extensions](BaseModel-Extensions.md).

## Overview and Architecture

The ModelSerializer system consists of three primary components: a metaclass that generates Pydantic models, a base model class that handles database operations, and a creator function that bridges Tortoise ORM fields to Pydantic field types.

```mermaid
flowchart TD

UserModel["Tortoise Model Definition<br>class MyModel(BaseModel)"]
UserSerializer["ModelSerializer Definition<br>class MySerializer(ModelSerializer)"]
MetaClass["ModelSerializerMetaclass<br>new()"]
Creator["pydantic_model_creator()<br>Field mapping & validation"]
PydanticGen["Generated Pydantic Model<br>with validation rules"]
SerializerInstance["ModelSerializer Instance<br>Validation & conversion"]
DatabaseOps["Database Operations<br>save(), to_model()"]
QuerysetOps["Queryset Operations<br>from_tortoise_orm(), from_queryset()"]

UserModel --> Creator
UserSerializer --> MetaClass
PydanticGen --> SerializerInstance

subgraph subGraph2 ["Runtime Operations"]
    SerializerInstance
    DatabaseOps
    QuerysetOps
    SerializerInstance --> DatabaseOps
    SerializerInstance --> QuerysetOps
end

subgraph subGraph1 ["Metaclass Processing"]
    MetaClass
    Creator
    PydanticGen
    MetaClass --> Creator
    Creator --> PydanticGen
end

subgraph subGraph0 ["User Definition"]
    UserModel
    UserSerializer
end
```

**Sources:** [fastapp/serializers/model.py L431-L517](/fastapp/serializers/model.py#L431-L517)

 [fastapp/serializers/creator.py L69-L545](/fastapp/serializers/creator.py#L69-L545)

## ModelSerializer Class Definition

The `ModelSerializer` class uses a metaclass pattern to automatically generate Pydantic models from Tortoise ORM models. Users define a simple class with a `Meta` inner class specifying the model and field configuration.

```mermaid
flowchart TD

MetaClass["Meta Class<br>model, fields, exclude"]
ReadOnly["read_only_fields<br>write_only_fields"]
Hidden["hidden_fields<br>depth settings"]
PydanticModel["ModelSerializerPydanticModel<br>Base functionality"]
FieldMap["field_map<br>Field descriptions"]
ModelConfig["model_config<br>Validation rules"]
ToModel["to_model()<br>Convert to ORM instance"]
Save["save()<br>Persist to database"]
FromORM["from_tortoise_orm()<br>Create from ORM object"]

MetaClass --> PydanticModel
ReadOnly --> ModelConfig
Hidden --> ModelConfig
PydanticModel --> ToModel
PydanticModel --> Save
PydanticModel --> FromORM
FieldMap --> ToModel

subgraph subGraph2 ["Core Methods"]
    ToModel
    Save
    FromORM
end

subgraph subGraph1 ["Generated Components"]
    PydanticModel
    FieldMap
    ModelConfig
end

subgraph subGraph0 ["Meta Configuration"]
    MetaClass
    ReadOnly
    Hidden
end
```

**Sources:** [fastapp/serializers/model.py L501-L517](/fastapp/serializers/model.py#L501-L517)

 [fastapp/serializers/model.py L431-L497](/fastapp/serializers/model.py#L431-L497)

## Pydantic Model Creation Process

The `pydantic_model_creator` function performs the complex task of analyzing a Tortoise model and generating a corresponding Pydantic model with appropriate field types, validation rules, and relationship handling.

```mermaid
flowchart TD

TortoiseModel["Tortoise Model<br>cls.describe()"]
FieldMap["Field Mapping<br>data_fields, fk_fields, m2m_fields"]
MetaConfig["Meta Configuration<br>include, exclude, depth"]
DataFields["Data Fields<br>Basic types, validation"]
RelationFields["Relationship Fields<br>ForeignKey, OneToOne, ManyToMany"]
ComputedFields["Computed Fields<br>Methods as properties"]
ExtraFields["Extra Fields<br>Custom serializer fields"]
PropertyMap["Property Mapping<br>Python types to Pydantic"]
ValidationRules["Validation Rules<br>Required, optional, nullable"]
ModelCreation["create_model()<br>Dynamic Pydantic model"]

FieldMap --> DataFields
FieldMap --> RelationFields
FieldMap --> ComputedFields
MetaConfig --> ExtraFields
DataFields --> PropertyMap
RelationFields --> PropertyMap
ComputedFields --> PropertyMap
ExtraFields --> PropertyMap

subgraph subGraph2 ["Pydantic Generation"]
    PropertyMap
    ValidationRules
    ModelCreation
    PropertyMap --> ValidationRules
    ValidationRules --> ModelCreation
end

subgraph subGraph1 ["Field Processing"]
    DataFields
    RelationFields
    ComputedFields
    ExtraFields
end

subgraph subGraph0 ["Model Analysis"]
    TortoiseModel
    FieldMap
    MetaConfig
    TortoiseModel --> FieldMap
end
```

**Sources:** [fastapp/serializers/creator.py L69-L123](/fastapp/serializers/creator.py#L69-L123)

 [fastapp/serializers/creator.py L301-L545](/fastapp/serializers/creator.py#L301-L545)

## Field Type Mapping and Validation

The system maps Tortoise ORM field types to corresponding Pydantic field types, handling validation constraints, nullable fields, and default values automatically.

| Tortoise Field | Pydantic Type | Validation Features |
| --- | --- | --- |
| `CharField` | `constr(max_length=...)` | Length validation |
| `IntField` | `int` | Type validation |
| `DateTimeField` | `datetime` | Format validation, auto_now handling |
| `JSONField` | `Any` | JSON serialization |
| `ForeignKeyField` | `Optional[SubModel]` | Nested model validation |
| `ManyToManyField` | `List[SubModel]` | List of nested models |

```mermaid
flowchart TD

TortoiseField["Tortoise Field<br>field.describe()"]
Constraints["Constraints<br>nullable, max_length, choices"]
DefaultValue["Default Values<br>auto_now, computed"]
PythonType["Python Type<br>str, int, datetime"]
Optional["Optional Wrapper<br>Union[Type, None]"]
FieldConfig["Field Configuration<br>default, validation"]
Relations["Relationship Fields<br>Nested model creation"]
JSONHandling["JSON Fields<br>Any type with serialization"]
ComputedProps["Computed Properties<br>@computed_field decorator"]

TortoiseField --> PythonType
Constraints --> Optional
DefaultValue --> FieldConfig
PythonType --> Relations
PythonType --> JSONHandling
PythonType --> ComputedProps

subgraph subGraph2 ["Special Handling"]
    Relations
    JSONHandling
    ComputedProps
end

subgraph subGraph1 ["Pydantic Mapping"]
    PythonType
    Optional
    FieldConfig
end

subgraph subGraph0 ["Field Analysis"]
    TortoiseField
    Constraints
    DefaultValue
end
```

**Sources:** [fastapp/serializers/creator.py L431-L479](/fastapp/serializers/creator.py#L431-L479)

 [fastapp/serializers/creator.py L60-L66](/fastapp/serializers/creator.py#L60-L66)

## Database Operations and Model Conversion

The ModelSerializer provides methods for converting between Pydantic models and Tortoise ORM instances, handling complex relationships and database transactions.

```mermaid
sequenceDiagram
  participant Client
  participant ModelSerializer
  participant to_model()
  participant Tortoise ORM
  participant Transaction Manager

  Client->>ModelSerializer: Create with data
  ModelSerializer->>ModelSerializer: Validate with Pydantic
  Client->>ModelSerializer: save()
  ModelSerializer->>to_model(): Convert to ORM instance
  to_model()->>Transaction Manager: Begin transaction
  to_model()->>Tortoise ORM: Save main instance
  to_model()->>Tortoise ORM: Handle M2M relations
  to_model()->>Tortoise ORM: Handle backward FK relations
  Transaction Manager->>to_model(): Commit transaction
  to_model()->>Client: Return saved instance
```

**Sources:** [fastapp/serializers/model.py L221-L264](/fastapp/serializers/model.py#L221-L264)

 [fastapp/serializers/model.py L155-L219](/fastapp/serializers/model.py#L155-L219)

## Relationship Handling

The system automatically handles complex relationships between models, supporting nested creation, updates, and validation of related objects.

```mermaid
flowchart TD

ForeignKey["ForeignKey Fields<br>Single related object"]
OneToOne["OneToOne Fields<br>Single bidirectional"]
ManyToMany["ManyToMany Fields<br>Multiple related objects"]
BackwardFK["Backward FK Relations<br>Reverse relationships"]
NestedCreate["Nested Creation<br>Create related objects"]
NestedUpdate["Nested Updates<br>Update existing relations"]
IDReference["ID References<br>Link by primary key"]
MainSave["Save Main Instance<br>Primary object first"]
RelationSave["Save Relations<br>Handle dependencies"]
Rollback["Error Handling<br>Transaction rollback"]

ForeignKey --> NestedCreate
OneToOne --> NestedUpdate
ManyToMany --> IDReference
BackwardFK --> NestedCreate
NestedCreate --> MainSave
NestedUpdate --> RelationSave
IDReference --> RelationSave

subgraph subGraph2 ["Transaction Management"]
    MainSave
    RelationSave
    Rollback
    MainSave --> Rollback
    RelationSave --> Rollback
end

subgraph subGraph1 ["Nested Operations"]
    NestedCreate
    NestedUpdate
    IDReference
end

subgraph subGraph0 ["Relationship Types"]
    ForeignKey
    OneToOne
    ManyToMany
    BackwardFK
end
```

**Sources:** [fastapp/serializers/model.py L266-L340](/fastapp/serializers/model.py#L266-L340)

 [fastapp/serializers/model.py L170-L182](/fastapp/serializers/model.py#L170-L182)

## Read-Only, Write-Only, and Hidden Fields

The system supports sophisticated field visibility and access control through configuration options in the Meta class.

| Field Type | API Input | API Output | Database | Use Case |
| --- | --- | --- | --- | --- |
| Normal | ✓ | ✓ | ✓ | Standard fields |
| Read-Only | ✗ | ✓ | - | Computed values, timestamps |
| Write-Only | ✓ | ✗ | ✓ | Passwords, sensitive data |
| Hidden | ✗ | ✗ | ✓ | Internal system fields |

**Sources:** [fastapp/serializers/model.py L124-L133](/fastapp/serializers/model.py#L124-L133)

 [fastapp/serializers/creator.py L174-L198](/fastapp/serializers/creator.py#L174-L198)

## Advanced Features

### Prefetching and Performance Optimization

The system includes automatic relationship prefetching to avoid N+1 query problems when serializing multiple objects.

```mermaid
flowchart TD

FetchFields["_get_fetch_fields()<br>Analyze required relations"]
Prefetch["prefetch_related()<br>Batch load relations"]
FromQueryset["from_queryset()<br>Bulk serialization"]
BatchLoad["Batch Loading<br>Single query per relation type"]
CacheFields["Field Caching<br>Avoid repeated analysis"]
LazyLoad["Lazy Loading<br>On-demand field access"]

FromQueryset --> BatchLoad
Prefetch --> CacheFields

subgraph subGraph1 ["Performance Features"]
    BatchLoad
    CacheFields
    LazyLoad
    BatchLoad --> LazyLoad
end

subgraph subGraph0 ["Query Optimization"]
    FetchFields
    Prefetch
    FromQueryset
    FetchFields --> Prefetch
    Prefetch --> FromQueryset
end
```

**Sources:** [fastapp/serializers/model.py L44-L76](/fastapp/serializers/model.py#L44-L76)

 [fastapp/serializers/model.py L378-L392](/fastapp/serializers/model.py#L378-L392)

### Custom Field Serialization

The system supports custom field types through the serializer fields module, allowing for specialized validation and serialization logic.

**Sources:** [fastapp/serializers/fields/__init__.py L180-L221](/fastapp/serializers/fields/__init__.py#L180-L221)

 [fastapp/serializers/creator.py L386-L407](/fastapp/serializers/creator.py#L386-L407)

## Integration with ViewSets

ModelSerializers integrate seamlessly with the ViewSet system to provide automatic CRUD API endpoints with validation and error handling.

```mermaid
flowchart TD

ViewSet["ModelViewSet<br>CRUD endpoints"]
Request["HTTP Request<br>JSON payload"]
Response["HTTP Response<br>Serialized data"]
Serializer["ModelSerializer<br>Validation & conversion"]
PydanticModel["Generated Pydantic Model<br>Type safety"]
ORM["Tortoise ORM<br>Database operations"]
Model["BaseModel<br>Enhanced features"]

Request --> Serializer
ViewSet --> Serializer
PydanticModel --> ORM
Model --> Response

subgraph subGraph2 ["Data Layer"]
    ORM
    Model
    ORM --> Model
end

subgraph subGraph1 ["Serialization Layer"]
    Serializer
    PydanticModel
    Serializer --> PydanticModel
end

subgraph subGraph0 ["API Layer"]
    ViewSet
    Request
    Response
end
```

**Sources:** [fastapp/serializers/model.py L1-L42](/fastapp/serializers/model.py#L1-L42)

 Integration details referenced from system architecture overview.