# Authentication and Authorization

> **Relevant source files**
> * [fastapp/contrib/auth/filters.py](/fastapp/contrib/auth/filters.py)
> * [fastapp/contrib/auth/serializers.py](/fastapp/contrib/auth/serializers.py)
> * [fastapp/contrib/auth/utils.py](/fastapp/contrib/auth/utils.py)
> * [fastapp/contrib/auth/validators.py](/fastapp/contrib/auth/validators.py)
> * [fastapp/contrib/auth/views.py](/fastapp/contrib/auth/views.py)

This document covers the JWT-based authentication system and role-based authorization mechanisms in QingKongFramework. The authentication system provides token-based user authentication with configurable user models, dependency injection for request authentication, and comprehensive admin interfaces for user and group management.

For information about API ViewSet permissions and pagination, see [Pagination and Permissions](Pagination-and-Permissions.md). For details on middleware and request processing, see [Framework Architecture](Framework-Architecture.md).

## JWT Token Authentication System

QingKongFramework implements a JWT-based authentication system with access and refresh token support. The token system uses version checking to invalidate tokens when user passwords change.

### Token Flow

```mermaid
sequenceDiagram
  participant Client
  participant TokenObtain["/token/"]
  participant TokenRefresh["/token/refresh/"]
  participant TokenVerify["/token/verify/"]
  participant AuthenticateUser["authenticate_user()"]
  participant CreateToken["create_token()"]
  participant TokenObtain
  participant AuthenticateUser
  participant CreateToken
  participant TokenRefresh
  participant TokenVerify

  Client->>TokenObtain: "POST username, password"
  TokenObtain->>AuthenticateUser: "verify credentials"
  AuthenticateUser-->>TokenObtain: "user object"
  TokenObtain->>CreateToken: "create ACCESS token"
  TokenObtain->>CreateToken: "create REFRESH token"
  CreateToken-->>TokenObtain: "signed tokens"
  TokenObtain-->>Client: "access + refresh tokens"
  note over Client: "Use access token for API calls"
  Client->>TokenRefresh: "POST refresh token"
  TokenRefresh->>CreateToken: "create new ACCESS token"
  TokenRefresh-->>Client: "new access token"
  Client->>TokenVerify: "POST any token"
  TokenVerify-->>Client: "payload + username"
```

Sources: [fastapp/contrib/auth/views.py L56-L91](/fastapp/contrib/auth/views.py#L56-L91)

 [fastapp/contrib/auth/views.py L94-L119](/fastapp/contrib/auth/views.py#L94-L119)

 [fastapp/contrib/auth/views.py L122-L138](/fastapp/contrib/auth/views.py#L122-L138)

### Token Types and Configuration

The system uses two token types defined in `TokenTypeEnum`:

| Token Type | Purpose | Lifetime Setting | Usage |
| --- | --- | --- | --- |
| `ACCESS` | API authentication | `ACCESS_TOKEN_LIFETIME` | Bearer token for API calls |
| `REFRESH` | Token renewal | `REFRESH_TOKEN_LIFETIME` | Renew access tokens |

Sources: [fastapp/contrib/auth/utils.py L20-L23](/fastapp/contrib/auth/utils.py#L20-L23)

### Version Checking

Tokens include a version hash based on the user's password to automatically invalidate all tokens when passwords change:

```mermaid
flowchart TD

CreateToken["create_token()"]
VersionKey["version_key=user.password"]
Blake2sHash["blake2s(password).digest()"]
Base85Encode["base64.b85encode()"]
TokenPayload["JWT payload.ver"]
ValidateToken["validate token"]
ExtractVer["extract payload.ver"]
CheckVersion["default_version_checker()"]
CurrentPassword["hash current password"]
CompareVersions["ver == current_hash"]
ValidToken["token valid"]
InvalidToken["token invalid"]

CreateToken --> VersionKey
VersionKey --> Blake2sHash
Blake2sHash --> Base85Encode
Base85Encode --> TokenPayload
ValidateToken --> ExtractVer
ExtractVer --> CheckVersion
CheckVersion --> CurrentPassword
CurrentPassword --> CompareVersions
CompareVersions --> ValidToken
CompareVersions --> InvalidToken
```

Sources: [fastapp/contrib/auth/views.py L78-L84](/fastapp/contrib/auth/views.py#L78-L84)

 [fastapp/contrib/auth/utils.py L129-L135](/fastapp/contrib/auth/utils.py#L129-L135)

## User Model and Configuration

### Configurable User Model

The framework supports configurable user models through the `AUTH_USER_MODEL` setting, similar to Django's approach:

```mermaid
flowchart TD

AuthUserModel["AUTH_USER_MODEL setting"]
ImportString["import_string()"]
UserModel["User model class"]
UserProtocol["UserProtocol interface"]
GetUserModel["get_user_model()"]
Views["API views"]
Dependencies["Auth dependencies"]

AuthUserModel --> ImportString
ImportString --> UserModel
UserModel --> UserProtocol
GetUserModel --> AuthUserModel
Views --> GetUserModel
Dependencies --> GetUserModel
```

Sources: [fastapp/contrib/auth/utils.py L28-L42](/fastapp/contrib/auth/utils.py#L28-L42)

### User Authentication

The authentication process validates username and password against the configured user model:

```mermaid
flowchart TD

AuthenticateUser["authenticate_user()"]
GetUser["get_user(username)"]
UserActive["user.is_active"]
ReturnNone["return None"]
VerifyPassword["verify_password()"]
CheckPassword["check_password()"]
DjangoHashers["Django password hashers"]
ReturnUser["return user"]

AuthenticateUser --> GetUser
GetUser --> UserActive
UserActive --> ReturnNone
UserActive --> VerifyPassword
VerifyPassword --> CheckPassword
CheckPassword --> DjangoHashers
DjangoHashers --> ReturnUser
DjangoHashers --> ReturnNone
```

Sources: [fastapp/contrib/auth/utils.py L68-L79](/fastapp/contrib/auth/utils.py#L68-L79)

 [fastapp/contrib/auth/utils.py L61-L65](/fastapp/contrib/auth/utils.py#L61-L65)

## Authentication Dependencies

QingKongFramework provides FastAPI dependency injection for authentication using factory functions that generate dependencies:

### Dependency Types

```mermaid
flowchart TD

GetCurrentUserFactory["get_current_user_factory()"]
CurrentUser["CurrentUser"]
CurrentSuperUser["CurrentSuperUser"]
OptionalCurrentUser["OptionalCurrentUser"]
RefreshTokenUser["RefreshTokenUser"]
RawToken["RawToken"]
AccessToken["ACCESS token required"]
VersionCheck["version checking"]
SuperuserCheck["is_superuser check"]
NoException["raise_exception=False"]
RefreshToken["REFRESH token required"]
RawPayload["returns (payload, user)"]

GetCurrentUserFactory --> CurrentUser
GetCurrentUserFactory --> CurrentSuperUser
GetCurrentUserFactory --> OptionalCurrentUser
GetCurrentUserFactory --> RefreshTokenUser
GetCurrentUserFactory --> RawToken
CurrentUser --> AccessToken
CurrentUser --> VersionCheck
CurrentSuperUser --> SuperuserCheck
OptionalCurrentUser --> NoException
RefreshTokenUser --> RefreshToken
RawToken --> RawPayload
```

Sources: [fastapp/contrib/auth/utils.py L156-L197](/fastapp/contrib/auth/utils.py#L156-L197)

### Dependency Factory Parameters

| Parameter | Type | Purpose |
| --- | --- | --- |
| `token_type` | `TokenTypeEnum` | Filter by ACCESS/REFRESH tokens |
| `raw` | `bool` | Return `(payload, user)` tuple |
| `raise_exception` | `bool` | Raise HTTP 401 on auth failure |
| `extra_action` | `Callable` | Additional validation (e.g., superuser check) |
| `version_checker` | `Callable` | Token version validation function |

Sources: [fastapp/contrib/auth/utils.py L82-L87](/fastapp/contrib/auth/utils.py#L82-L87)

## Admin User and Group Management

### Admin User ViewSet

The `AdminUserViewSet` provides comprehensive user management for superusers:

```mermaid
flowchart TD

AdminUserViewSet["AdminUserViewSet"]
SuperUserMixin["SuperUserRequiredMixin"]
ModelViewSet["ModelViewSet"]
UserFilterSet["UserFilterSet"]
CreateUser["POST /users/"]
UpdateUser["PUT/PATCH /users/{id}/"]
DeleteUser["DELETE /users/{id}/"]
ChangePassword["POST /users/{id}/change-password/"]
EmailValidation["email uniqueness check"]
SetPassword["user.set_password()"]

AdminUserViewSet --> SuperUserMixin
AdminUserViewSet --> ModelViewSet
AdminUserViewSet --> UserFilterSet
AdminUserViewSet --> CreateUser
AdminUserViewSet --> UpdateUser
AdminUserViewSet --> DeleteUser
AdminUserViewSet --> ChangePassword
CreateUser --> EmailValidation
UpdateUser --> EmailValidation
ChangePassword --> SetPassword
```

Sources: [fastapp/contrib/auth/views.py L246-L303](/fastapp/contrib/auth/views.py#L246-L303)

### Admin Group ViewSet

The `AdminGroupViewSet` manages groups and group membership:

```mermaid
flowchart TD

AdminGroupViewSet["AdminGroupViewSet"]
GroupCRUD["Group CRUD operations"]
ListUsers["GET /groups/{id}/user/"]
AddUsers["POST /groups/{id}/user/"]
RemoveUsers["DELETE /groups/{id}/user/"]
UserSet["group.user_set.all()"]
UserIDsSerializer["UserIDsSerializer validation"]
GroupUserAdd["group.user_set.add(*users)"]
GroupUserRemove["group.user_set.remove(*users)"]

AdminGroupViewSet --> GroupCRUD
AdminGroupViewSet --> ListUsers
AdminGroupViewSet --> AddUsers
AdminGroupViewSet --> RemoveUsers
ListUsers --> UserSet
AddUsers --> UserIDsSerializer
AddUsers --> GroupUserAdd
RemoveUsers --> UserIDsSerializer
RemoveUsers --> GroupUserRemove
```

Sources: [fastapp/contrib/auth/views.py L305-L406](/fastapp/contrib/auth/views.py#L305-L406)

## Permission System

### Superuser Required Mixin

The `SuperUserRequiredMixin` restricts access to superusers through the dependency injection system:

```mermaid
flowchart TD

SuperUserMixin["SuperUserRequiredMixin"]
CurrentSuperUser["CurrentSuperUser dependency"]
IsSuperuser["is_superuser() check"]
AllowAccess["allow access"]
HTTP401["HTTP 401 Unauthorized"]
AdminUserViewSet["AdminUserViewSet"]
AdminGroupViewSet["AdminGroupViewSet"]

SuperUserMixin --> CurrentSuperUser
CurrentSuperUser --> IsSuperuser
IsSuperuser --> AllowAccess
IsSuperuser --> HTTP401
AdminUserViewSet --> SuperUserMixin
AdminGroupViewSet --> SuperUserMixin
```

Sources: [fastapp/contrib/auth/views.py L246](/fastapp/contrib/auth/views.py#L246-L246)

 [fastapp/contrib/auth/views.py L305](/fastapp/contrib/auth/views.py#L305-L305)

 [fastapp/contrib/auth/utils.py L138-L154](/fastapp/contrib/auth/utils.py#L138-L154)

## Password Management and Validation

### User Password Change

The framework provides both user-initiated and admin password changes:

```mermaid
flowchart TD

UserChangePassword["/change-password/"]
CurrentUser["authenticate current user"]
ValidateOldPassword["verify old password"]
ValidateNewPassword["validate new password complexity"]
CheckUsername["new password != username"]
MakePassword["make_password()"]
SaveUser["user.save()"]
AdminChangePassword["/users/{id}/change-password/"]
SuperUserCheck["superuser required"]
SetPassword["user.set_password()"]

UserChangePassword --> CurrentUser
CurrentUser --> ValidateOldPassword
ValidateOldPassword --> ValidateNewPassword
ValidateNewPassword --> CheckUsername
CheckUsername --> MakePassword
MakePassword --> SaveUser
AdminChangePassword --> SuperUserCheck
SuperUserCheck --> SetPassword
SetPassword --> SaveUser
```

Sources: [fastapp/contrib/auth/views.py L195-L222](/fastapp/contrib/auth/views.py#L195-L222)

 [fastapp/contrib/auth/views.py L267-L279](/fastapp/contrib/auth/views.py#L267-L279)

### Password Validation

Password complexity is enforced through multiple validators:

| Validation Rule | Implementation |
| --- | --- |
| Minimum length | 8+ characters |
| Uppercase letter | At least one A-Z |
| Lowercase letter | At least one a-z |
| Digit | At least one 0-9 |
| Special character | `!@#$%^&*()-_=+[]{}` etc. |
| Username check | Cannot contain username |

Sources: [fastapp/contrib/auth/validators.py L18-L43](/fastapp/contrib/auth/validators.py#L18-L43)

 [fastapp/contrib/auth/views.py L167-L192](/fastapp/contrib/auth/views.py#L167-L192)

### User Profile and Session Management

The authentication system provides profile access and logout functionality:

```mermaid
flowchart TD

Profile["/profile/"]
CurrentUser["CurrentUser dependency"]
UserSerializer["UserSerializer.model_validate()"]
ExcludePassword["exclude password field"]
Logout["/logout/"]
DeleteCookies["response.delete_cookie()"]
ClearSession["clear all request cookies"]

Profile --> CurrentUser
CurrentUser --> UserSerializer
UserSerializer --> ExcludePassword
Logout --> DeleteCookies
DeleteCookies --> ClearSession
```

Sources: [fastapp/contrib/auth/views.py L141-L152](/fastapp/contrib/auth/views.py#L141-L152)

 [fastapp/contrib/auth/views.py L225-L243](/fastapp/contrib/auth/views.py#L225-L243)

 [fastapp/contrib/auth/serializers.py L16-L25](/fastapp/contrib/auth/serializers.py#L16-L25)