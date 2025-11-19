# Development and Utility Commands

> **Relevant source files**
> * [fastapp/commands/load_data.py](/fastapp/commands/load_data.py)
> * [fastapp/commands/user.py](/fastapp/commands/user.py)
> * [fastapp/misc/gateway.py](/fastapp/misc/gateway.py)
> * [fastapp/misc/serve_static.py](/fastapp/misc/serve_static.py)
> * [fastapp/utils/json.py](/fastapp/utils/json.py)
> * [manage.py](/manage.py)
> * [pyproject.toml](/pyproject.toml)
> * [setup-pure.py](/setup-pure.py)

This document covers the development and utility commands in QingKongFramework's CLI system. These commands support the development workflow by providing application scaffolding, user management, data loading, and system information utilities.

For server management commands like `runserver` and `gateway`, see [Server Commands](Server-Commands.md). For database management commands like `migrate` and `auto_migrate`, see [Database Commands](Database-Commands.md).

## Command Overview

QingKongFramework provides several development-focused commands that streamline the application development process:

| Command | Purpose | Primary Use Case |
| --- | --- | --- |
| `startapp` | Application scaffolding | Creating new app modules |
| `loaddata` | Fixture data loading | Populating databases with test/initial data |
| `createsuperuser` | Admin user creation | Setting up administrative access |
| `about` | System information | Displaying framework and environment info |

### Command Registration Architecture

```mermaid
flowchart TD

ManagePy["manage.py"]
CLI["fastapp.commands.cli"]
RegisterCommands["cli.register_commands()"]
StartApp["startapp"]
About["about"]
ServeStatic["serve_static"]
LoadData["loaddata"]
CreateSuperuser["createsuperuser"]
RunServer["runserver"]
Gateway["gateway"]
Migrate["migrate"]

ManagePy --> CLI
RegisterCommands --> StartApp
RegisterCommands --> About
RegisterCommands --> ServeStatic
RegisterCommands --> LoadData
RegisterCommands --> CreateSuperuser
RegisterCommands --> RunServer
RegisterCommands --> Gateway
RegisterCommands --> Migrate

subgraph subGraph4 ["Infrastructure Commands"]
    RunServer
    Gateway
    Migrate
end

subgraph subGraph3 ["Utility Commands"]
    LoadData
    CreateSuperuser
end

subgraph subGraph2 ["Development Commands"]
    StartApp
    About
    ServeStatic
end

subgraph subGraph1 ["Command Registration"]
    CLI
    RegisterCommands
    CLI --> RegisterCommands
end

subgraph subGraph0 ["CLI Entry Point"]
    ManagePy
end
```

Sources: [manage.py L3-L5](/manage.py#L3-L5)

## Application Scaffolding

### startapp Command

The `startapp` command creates the directory structure for new applications within the QingKongFramework project. While the implementation file is not visible in the provided sources, this command follows Django-like conventions for creating modular applications.

Expected application structure created by `startapp`:

```mermaid
flowchart TD

AppDir["apps/{app_name}/"]
Models["models.py"]
Views["views.py"]
Serializers["serializers.py"]
Filters["filters.py"]
URLs["urls.py"]
Fixtures["fixtures/"]
Init["init.py"]
Settings["settings.INSTALLED_APPS"]
AppsConfig["fastapp.initialize.apps"]
Discovery["Application Discovery"]

AppDir --> Settings

subgraph subGraph1 ["Integration Points"]
    Settings
    AppsConfig
    Discovery
    Settings --> AppsConfig
    AppsConfig --> Discovery
end

subgraph subGraph0 ["Generated App Structure"]
    AppDir
    Models
    Views
    Serializers
    Filters
    URLs
    Fixtures
    Init
    AppDir --> Models
    AppDir --> Views
    AppDir --> Serializers
    AppDir --> Filters
    AppDir --> URLs
    AppDir --> Fixtures
    AppDir --> Init
end
```

Sources: [manage.py L3-L5](/manage.py#L3-L5)

## Data Management Commands

### loaddata Command

The `loaddata` command loads fixture data from JSON or JSONC files into the database. It provides sophisticated handling of relationships and supports bulk loading operations.

```mermaid
flowchart TD

FileArg["file_path argument"]
AllOption["'all' option"]
SpecificFile["specific file path"]
FindFiles["find_file_in_fixtures()"]
GetAllFixtures["get_all_fixtures()"]
AppDirs["apps/*/fixtures/"]
SearchPattern["*.json, *.jsonc files"]
RemoveComments["remove_comments()"]
JSONParse["json.loads()"]
HandleFields["_handle_fields()"]
FKResolution["Foreign Key Resolution"]
M2MProcessing["Many-to-Many Processing"]
ModelLookup["Tortoise.apps.get()"]
InstanceCreation["model(**fields)"]
SaveOperation["instance.save()"]
SequenceUpdate["PostgreSQL sequence update"]

AllOption --> GetAllFixtures
SpecificFile --> FindFiles
SearchPattern --> RemoveComments
FKResolution --> ModelLookup
M2MProcessing --> ModelLookup

subgraph subGraph3 ["Database Operations"]
    ModelLookup
    InstanceCreation
    SaveOperation
    SequenceUpdate
    ModelLookup --> InstanceCreation
    InstanceCreation --> SaveOperation
    SaveOperation --> SequenceUpdate
end

subgraph subGraph2 ["Data Processing"]
    RemoveComments
    JSONParse
    HandleFields
    FKResolution
    M2MProcessing
    RemoveComments --> JSONParse
    JSONParse --> HandleFields
    HandleFields --> FKResolution
    HandleFields --> M2MProcessing
end

subgraph subGraph1 ["File Discovery"]
    FindFiles
    GetAllFixtures
    AppDirs
    SearchPattern
    FindFiles --> AppDirs
    GetAllFixtures --> AppDirs
    AppDirs --> SearchPattern
end

subgraph subGraph0 ["Command Input"]
    FileArg
    AllOption
    SpecificFile
    FileArg --> AllOption
    FileArg --> SpecificFile
end
```

Sources: [fastapp/commands/load_data.py L17-L224](/fastapp/commands/load_data.py#L17-L224)

#### Fixture File Format

The `loaddata` command supports JSON and JSONC (JSON with comments) fixture files with the following structure:

```json
[
  {
    "model": "app_name.ModelName",
    "pk": 1,
    "fields": {
      "field_name": "value",
      "foreign_key_field": "${field=value}",
      "many_to_many_field": [1, 2, 3]
    }
  }
]
```

Key features:

| Feature | Syntax | Purpose |
| --- | --- | --- |
| Foreign Key Reference | `"${field=value}"` | Reference related objects by field values |
| Many-to-Many Relations | `[1, 2, 3]` | List of related object IDs |
| JSONC Comments | `//` or `/* */` | Documentation within fixture files |
| Sequence Updates | Automatic | PostgreSQL sequence synchronization |

### File Discovery Logic

The command searches for fixture files using a hierarchical approach:

```mermaid
flowchart TD

StartSearch["Start Search"]
CheckSpecific["Check Specific Path"]
SearchApps["Search App Directories"]
CheckMultiple["Check for Duplicates"]
ReturnPath["Return File Path"]
AppsFilter["Filter INSTALLED_APPS"]
AppPaths["apps/* directories"]
FixturesDir["fixtures/ subdirectory"]
WalkTree["os.walk() traversal"]

SearchApps --> AppsFilter
WalkTree --> CheckMultiple

subgraph subGraph1 ["App Directory Structure"]
    AppsFilter
    AppPaths
    FixturesDir
    WalkTree
    AppsFilter --> AppPaths
    AppPaths --> FixturesDir
    FixturesDir --> WalkTree
end

subgraph subGraph0 ["Search Process"]
    StartSearch
    CheckSpecific
    SearchApps
    CheckMultiple
    ReturnPath
    StartSearch --> CheckSpecific
    CheckSpecific --> SearchApps
    CheckMultiple --> ReturnPath
end
```

Sources: [fastapp/commands/load_data.py L17-L40](/fastapp/commands/load_data.py#L17-L40)

 [fastapp/commands/load_data.py L42-L57](/fastapp/commands/load_data.py#L42-L57)

## User Management Commands

### createsuperuser Command

The `createsuperuser` command creates administrative users for the application. It integrates with the authentication system to create users with superuser privileges.

```mermaid
flowchart TD

CheckAuth["Check contrib.auth installed"]
CheckContentTypes["Check contrib.contenttypes installed"]
ValidationError["Raise error if missing"]
PromptUsername["input('Username: ')"]
PromptEmail["input('Email: ')"]
PromptPassword["getpass.getpass('Password: ')"]
ValidateLength["Validate password length >= 8"]
ConfirmPassword["getpass.getpass('Repeat Password: ')"]
CheckMatch["Verify passwords match"]
GetUserModel["get_user_model()"]
CreateUser["User.objects.create_user()"]
SetSuperuser["is_superuser=True"]
SaveUser["Save to database"]
InitApps["init_apps()"]
InitDB["async_init_db()"]
CloseConnections["Tortoise.close_connections()"]

CheckContentTypes --> InitApps
InitDB --> PromptUsername
CheckMatch --> GetUserModel
SaveUser --> CloseConnections

subgraph subGraph3 ["Database Setup"]
    InitApps
    InitDB
    CloseConnections
    InitApps --> InitDB
end

subgraph subGraph2 ["User Creation"]
    GetUserModel
    CreateUser
    SetSuperuser
    SaveUser
    GetUserModel --> CreateUser
    CreateUser --> SetSuperuser
    SetSuperuser --> SaveUser
end

subgraph subGraph1 ["User Input Collection"]
    PromptUsername
    PromptEmail
    PromptPassword
    ValidateLength
    ConfirmPassword
    CheckMatch
    PromptUsername --> PromptEmail
    PromptEmail --> PromptPassword
    PromptPassword --> ValidateLength
    ValidateLength --> ConfirmPassword
    ConfirmPassword --> CheckMatch
    CheckMatch --> PromptPassword
end

subgraph subGraph0 ["Prerequisites Check"]
    CheckAuth
    CheckContentTypes
    ValidationError
    CheckAuth --> CheckContentTypes
    CheckContentTypes --> ValidationError
end
```

Sources: [fastapp/commands/user.py L13-L49](/fastapp/commands/user.py#L13-L49)

### Password Validation

The command implements basic password validation:

| Validation Rule | Implementation | Error Message |
| --- | --- | --- |
| Minimum Length | `len(password) < 8` | "Password must be at least 8 characters long" |
| Password Match | `password != repeat_password` | Reprompt for password entry |
| Required Fields | Username, email, password | Interactive prompts |

Sources: [fastapp/commands/user.py L30-L37](/fastapp/commands/user.py#L30-L37)

## Development Workflow Integration

### Command Dependencies and Flow

```mermaid
flowchart TD

StartApp["manage.py startapp"]
AppStructure["Generated app files"]
ConfigUpdate["Update INSTALLED_APPS"]
CreateFixtures["Create fixture files"]
LoadData["manage.py loaddata"]
CreateSuperuser["manage.py createsuperuser"]
Migrate["manage.py migrate"]
AutoMigrate["manage.py auto_migrate"]
RunServer["manage.py runserver"]
TestApp["Test application"]

ConfigUpdate --> Migrate
Migrate --> CreateFixtures
CreateSuperuser --> RunServer

subgraph subGraph3 ["Development Server"]
    RunServer
    TestApp
    RunServer --> TestApp
end

subgraph subGraph2 ["Database Preparation"]
    Migrate
    AutoMigrate
    AutoMigrate --> Migrate
end

subgraph subGraph1 ["Development Data"]
    CreateFixtures
    LoadData
    CreateSuperuser
    CreateFixtures --> LoadData
    LoadData --> CreateSuperuser
end

subgraph subGraph0 ["Project Setup"]
    StartApp
    AppStructure
    ConfigUpdate
    StartApp --> AppStructure
    AppStructure --> ConfigUpdate
end
```

Sources: [manage.py L3-L9](/manage.py#L3-L9)

 [fastapp/commands/load_data.py L196-L197](/fastapp/commands/load_data.py#L196-L197)

 [fastapp/commands/user.py L21-L22](/fastapp/commands/user.py#L21-L22)

### Integration with Framework Components

The development commands integrate with several framework systems:

| Command | Framework Integration | Key Dependencies |
| --- | --- | --- |
| `startapp` | Application discovery system | `settings.INSTALLED_APPS` |
| `loaddata` | ORM and model system | `BaseModel`, `Tortoise.apps` |
| `createsuperuser` | Authentication system | `contrib.auth`, `get_user_model()` |
| `about` | System information | Framework version, environment |

Sources: [fastapp/commands/load_data.py L125-L127](/fastapp/commands/load_data.py#L125-L127)

 [fastapp/commands/user.py L15-L17](/fastapp/commands/user.py#L15-L17)