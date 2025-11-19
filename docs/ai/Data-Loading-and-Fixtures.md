# Data Loading and Fixtures

> **Relevant source files**
> * [fastapp/commands/load_data.py](/fastapp/commands/load_data.py)
> * [fastapp/commands/user.py](/fastapp/commands/user.py)
> * [fastapp/misc/gateway.py](/fastapp/misc/gateway.py)
> * [fastapp/misc/serve_static.py](/fastapp/misc/serve_static.py)
> * [fastapp/utils/json.py](/fastapp/utils/json.py)
> * [pyproject.toml](/pyproject.toml)
> * [setup-pure.py](/setup-pure.py)

## Purpose and Scope

This document covers QingKongFramework's data loading and fixture system, which provides Django-like functionality for populating databases with initial or test data. The system supports JSON and JSONC (JSON with comments) fixture files and handles complex relationships including foreign keys, many-to-many fields, and reverse foreign key associations.

For database migration and schema management, see [Database Migrations and Schema](Database-Migrations-and-Schema.md). For CLI command overview, see [Command Line Interface](Command-Line-Interface.md).

## Fixture System Overview

QingKongFramework's fixture system is built around the `loaddata` command, which discovers and loads JSON fixture files from application directories. The system integrates with the BaseModel extensions and Tortoise ORM to handle complex data relationships automatically.

### Fixture Loading Architecture

```mermaid
flowchart TD

loaddata_cmd["loaddata command"]
click_arg["file_path argument"]
find_file["find_file_in_fixtures()"]
get_all["get_all_fixtures()"]
fixtures_dir["apps/{app}/fixtures/"]
loaddata_inner["_loaddata_inner()"]
handle_fields["_handle_fields()"]
process_backward["process_backward_fk_fields()"]
save_backward["save_backward_fk_fields()"]
BaseModel_inst["BaseModel instances"]
tortoise_apps["Tortoise.apps"]
db_connection["Database connection"]
remove_comments_func["remove_comments()"]
json_parse["json.loads()"]

click_arg --> find_file
click_arg --> get_all
fixtures_dir --> loaddata_inner
loaddata_inner --> remove_comments_func
json_parse --> handle_fields
process_backward --> BaseModel_inst
BaseModel_inst --> save_backward
handle_fields --> tortoise_apps

subgraph subGraph4 ["JSON Processing"]
    remove_comments_func
    json_parse
    remove_comments_func --> json_parse
end

subgraph subGraph3 ["ORM Integration"]
    BaseModel_inst
    tortoise_apps
    db_connection
    BaseModel_inst --> db_connection
end

subgraph subGraph2 ["Data Processing Pipeline"]
    loaddata_inner
    handle_fields
    process_backward
    save_backward
    handle_fields --> process_backward
end

subgraph subGraph1 ["File Discovery"]
    find_file
    get_all
    fixtures_dir
    find_file --> fixtures_dir
    get_all --> fixtures_dir
end

subgraph subGraph0 ["CLI Interface"]
    loaddata_cmd
    click_arg
    loaddata_cmd --> click_arg
end
```

Sources: [fastapp/commands/load_data.py L1-L225](/fastapp/commands/load_data.py#L1-L225)

 [fastapp/utils/json.py L8-L40](/fastapp/utils/json.py#L8-L40)

## The loaddata Command

The `loaddata` command provides the primary interface for loading fixture data. It supports both individual file loading and batch processing of all fixtures in an application.

### Command Interface and Discovery

| Parameter | Type | Description |
| --- | --- | --- |
| `file_path` | STRING | Path to fixture file or "all" for batch loading |

The command performs automatic file discovery in application fixture directories:

```mermaid
flowchart TD

all_option["file_path == 'all'"]
get_all_fixtures_call["get_all_fixtures()"]
sort_by_prefix["Sort by numeric prefix"]
input_path["Input: file_path"]
check_exists["Check if file exists"]
search_apps["Search in INSTALLED_APPS"]
apps_filter["Filter apps starting with 'apps'"]
fixtures_search["Search in fixtures/ subdirs"]
found_file["Return found file path"]

subgraph subGraph1 ["Batch Processing"]
    all_option
    get_all_fixtures_call
    sort_by_prefix
    all_option --> get_all_fixtures_call
    get_all_fixtures_call --> sort_by_prefix
end

subgraph subGraph0 ["File Discovery Logic"]
    input_path
    check_exists
    search_apps
    apps_filter
    fixtures_search
    found_file
    input_path --> check_exists
    check_exists --> search_apps
    search_apps --> apps_filter
    apps_filter --> fixtures_search
    fixtures_search --> found_file
    check_exists --> found_file
end
```

Sources: [fastapp/commands/load_data.py L122-L136](/fastapp/commands/load_data.py#L122-L136)

 [fastapp/commands/load_data.py L199-L217](/fastapp/commands/load_data.py#L199-L217)

### Application Integration

The system integrates with the application discovery mechanism by searching through `INSTALLED_APPS` that start with "apps":

```mermaid
flowchart TD

installed_apps["settings.INSTALLED_APPS"]
app_filter["Filter: startswith('apps')"]
app_dirs["Convert to directory paths"]
app_dir["apps/{app_name}/"]
fixtures_dir["fixtures/"]
json_files[".json and .jsonc files"]
numeric_prefix["Numeric prefix sorting"]
filename_sort["Filename sorting"]
execution_order["Sequential execution"]

app_dirs --> app_dir
json_files --> numeric_prefix

subgraph subGraph2 ["File Processing Order"]
    numeric_prefix
    filename_sort
    execution_order
    numeric_prefix --> filename_sort
    filename_sort --> execution_order
end

subgraph subGraph1 ["Fixture Directory Structure"]
    app_dir
    fixtures_dir
    json_files
    app_dir --> fixtures_dir
    fixtures_dir --> json_files
end

subgraph subGraph0 ["Application Structure"]
    installed_apps
    app_filter
    app_dirs
    installed_apps --> app_filter
    app_filter --> app_dirs
end
```

Sources: [fastapp/commands/load_data.py L123-L128](/fastapp/commands/load_data.py#L123-L128)

 [fastapp/commands/load_data.py L200-L212](/fastapp/commands/load_data.py#L200-L212)

## Fixture File Format and Structure

Fixtures use JSON or JSONC (JSON with comments) format and follow a specific structure for defining model instances and their relationships.

### JSON Structure and Comment Support

The system supports JSONC format through the `remove_comments` utility, which strips both line comments (`//`) and block comments (`/* */`):

| Comment Type | Syntax | Processing |
| --- | --- | --- |
| Line comments | `// comment` | Removed from end of line |
| Block comments | `/* comment */` | Removed across multiple lines |

### Fixture Data Format

```mermaid
flowchart TD

root_array["Root: Array of objects"]
item_structure["Item structure"]
model_field["model: 'app.ModelName'"]
pk_field["pk: primary key (optional)"]
fields_object["fields: object with data"]
regular_fields["Regular model fields"]
fk_fields["Foreign key references"]
m2m_fields["Many-to-many arrays"]
backward_fk["Backward foreign keys"]
template_refs["Template references: ${field=value}"]

item_structure --> model_field
item_structure --> pk_field
item_structure --> fields_object
fields_object --> regular_fields
fields_object --> fk_fields
fields_object --> m2m_fields
fields_object --> backward_fk
fields_object --> template_refs

subgraph subGraph2 ["Field Types Supported"]
    regular_fields
    fk_fields
    m2m_fields
    backward_fk
    template_refs
end

subgraph subGraph1 ["Item Fields"]
    model_field
    pk_field
    fields_object
end

subgraph subGraph0 ["Fixture File Structure"]
    root_array
    item_structure
    root_array --> item_structure
end
```

Sources: [fastapp/commands/load_data.py L137-L143](/fastapp/commands/load_data.py#L137-L143)

 [fastapp/utils/json.py L8-L40](/fastapp/utils/json.py#L8-L40)

## Data Processing and Relationships

The fixture system handles complex ORM relationships through a multi-stage processing pipeline that resolves foreign keys, processes many-to-many relationships, and handles reverse associations.

### Foreign Key Resolution

The system supports template-based foreign key resolution using the syntax `${field=value}`:

```mermaid
flowchart TD

template_syntax["Template: ${field=value}"]
parse_template["Extract field and value"]
fk_lookup["Query related model"]
id_substitution["Replace with object.id"]
fk_fields_dict["_get_model_fk_id_fields_dict()"]
source_field["field.source_field"]
related_model["field.related_model"]

related_model --> fk_lookup

subgraph subGraph1 ["Field Type Detection"]
    fk_fields_dict
    source_field
    related_model
    fk_fields_dict --> source_field
    source_field --> related_model
end

subgraph subGraph0 ["Foreign Key Processing"]
    template_syntax
    parse_template
    fk_lookup
    id_substitution
    template_syntax --> parse_template
    parse_template --> fk_lookup
    fk_lookup --> id_substitution
end
```

Sources: [fastapp/commands/load_data.py L60-L78](/fastapp/commands/load_data.py#L60-L78)

 [fastapp/commands/load_data.py L76-L77](/fastapp/commands/load_data.py#L76-L77)

### Many-to-Many and Backward Relationships

The system processes complex relationships in multiple phases to handle dependencies correctly:

```mermaid
flowchart TD

phase1["Phase 1: Regular fields + FK resolution"]
phase2["Phase 2: Create/update instance"]
phase3["Phase 3: Handle backward FKs"]
phase4["Phase 4: Process M2M relationships"]
detect_backward["Detect backward_fk_fields"]
extract_reference["Extract reference field"]
defer_processing["Defer to after instance creation"]
update_related["Update related objects"]
detect_m2m["Detect m2m_fields"]
clear_existing["Clear existing relationships"]
add_new["Add new relationships"]

phase1 --> detect_backward
phase3 --> defer_processing
phase4 --> detect_m2m

subgraph subGraph2 ["M2M Processing"]
    detect_m2m
    clear_existing
    add_new
    detect_m2m --> clear_existing
    clear_existing --> add_new
end

subgraph subGraph1 ["Backward FK Processing"]
    detect_backward
    extract_reference
    defer_processing
    update_related
    detect_backward --> extract_reference
    extract_reference --> defer_processing
    defer_processing --> update_related
end

subgraph subGraph0 ["Relationship Processing Phases"]
    phase1
    phase2
    phase3
    phase4
    phase1 --> phase2
    phase2 --> phase3
    phase3 --> phase4
end
```

Sources: [fastapp/commands/load_data.py L83-L102](/fastapp/commands/load_data.py#L83-L102)

 [fastapp/commands/load_data.py L105-L119](/fastapp/commands/load_data.py#L105-L119)

 [fastapp/commands/load_data.py L173-L184](/fastapp/commands/load_data.py#L173-L184)

### Instance Creation and Update Logic

The system handles different scenarios for instance creation based on primary key presence and existence:

| Scenario | Primary Key | Exists in DB | Action |
| --- | --- | --- | --- |
| New without PK | `None` | N/A | Create new instance |
| Update existing | Present | Yes | Update existing instance |
| Create with PK | Present | No | Create with specified PK |

Sources: [fastapp/commands/load_data.py L150-L170](/fastapp/commands/load_data.py#L150-L170)

## Database-Specific Features

The fixture loading system includes database-specific optimizations and features, particularly for PostgreSQL.

### PostgreSQL Sequence Management

For PostgreSQL databases, the system automatically updates sequence values after loading data to prevent primary key conflicts:

```mermaid
flowchart TD

detect_pg["Detect PostgreSQL connection"]
get_table["Get model table name"]
sequence_query["Execute setval() query"]
max_id["Set sequence to MAX(id)"]
pg_get_serial["pg_get_serial_sequence()"]
coalesce_max["COALESCE(MAX(id), 1)"]
setval_func["setval() function"]

sequence_query --> pg_get_serial
sequence_query --> coalesce_max
sequence_query --> setval_func

subgraph subGraph1 ["Query Components"]
    pg_get_serial
    coalesce_max
    setval_func
end

subgraph subGraph0 ["PostgreSQL Sequence Update"]
    detect_pg
    get_table
    sequence_query
    max_id
    detect_pg --> get_table
    get_table --> sequence_query
    sequence_query --> max_id
end
```

Sources: [fastapp/commands/load_data.py L186-L193](/fastapp/commands/load_data.py#L186-L193)

## Integration with Framework Architecture

The fixture system integrates deeply with QingKongFramework's core components, leveraging the application discovery, database initialization, and model systems.

### System Dependencies

```mermaid
flowchart TD

settings_sys["settings.INSTALLED_APPS"]
init_apps["init_apps()"]
async_init_db["async_init_db()"]
tortoise_config["get_tortoise_config()"]
BaseModel_cls["BaseModel"]
tortoise_apps_registry["Tortoise.apps registry"]
meta_info["Model._meta information"]
field_types["Field type detection"]
loaddata_command["loaddata command"]
file_discovery["File discovery system"]
data_processing["Data processing pipeline"]

tortoise_config --> BaseModel_cls
init_apps --> loaddata_command
tortoise_apps_registry --> file_discovery
field_types --> data_processing

subgraph subGraph2 ["Fixture Processing"]
    loaddata_command
    file_discovery
    data_processing
end

subgraph subGraph1 ["Model System Integration"]
    BaseModel_cls
    tortoise_apps_registry
    meta_info
    field_types
    BaseModel_cls --> tortoise_apps_registry
    BaseModel_cls --> meta_info
    meta_info --> field_types
end

subgraph subGraph0 ["Core Dependencies"]
    settings_sys
    init_apps
    async_init_db
    tortoise_config
    settings_sys --> init_apps
    init_apps --> async_init_db
    async_init_db --> tortoise_config
end
```

Sources: [fastapp/commands/load_data.py L8-L14](/fastapp/commands/load_data.py#L8-L14)

 [fastapp/commands/load_data.py L196-L197](/fastapp/commands/load_data.py#L196-L197)