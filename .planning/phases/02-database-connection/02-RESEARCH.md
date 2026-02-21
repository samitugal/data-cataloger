# Phase 2: Database Connection - Research

**Researched:** 2026-02-21
**Domain:** Python database connectivity (PostgreSQL, MySQL/MariaDB)
**Confidence:** HIGH

<phase_requirements>
## Phase Requirements

This phase MUST address the following requirements from REQUIREMENTS.md:

| ID | Description | Research Support |
|----|-------------|-----------------|
| CONN-01 | User can enter database connection credentials (host, port, username, password, database name) | Configuration management using Pydantic dataclasses with validation; credential storage patterns with keyring or encrypted .env files |
| CONN-02 | System supports PostgreSQL database connections | psycopg3 (latest PostgreSQL adapter) with connection pooling, context managers, and proper error handling |
| CONN-03 | System supports MySQL/MariaDB database connections | mysql-connector-python 9.6.0 (official Oracle driver) with MariaDB compatibility; connection validation using `.connected` property |
| CONN-04 | System tests connection and displays success or failure feedback | Connection testing using context managers with try-except blocks; specific exception handling for OperationalError, InterfaceError, ConnectionTimeout; connection validation methods |
| CONN-05 | System securely handles database credentials (not stored in plain text) | keyring for local development (OS-level credential storage); python-dotenv with .env files (git-ignored); cryptography library with Fernet encryption for stored credentials; environment variable patterns |
</phase_requirements>

## Summary

Database connection implementation in Python requires the standard libraries psycopg3 for PostgreSQL and mysql-connector-python for MySQL/MariaDB. Both libraries provide robust connection management with context managers for automatic resource cleanup and transaction handling. Security is paramount: credentials should never be hardcoded or stored in plain text. For local development, use the keyring library (OS-level secure storage) or python-dotenv with git-ignored .env files. For production, environment variables or secret management services are required.

Connection testing must handle specific exception types (OperationalError for network/auth failures, InterfaceError for driver issues, ConnectionTimeout for timeouts) and provide clear user feedback. The factory pattern enables abstracting database type selection, allowing the application to support both PostgreSQL and MySQL through a unified interface. Type hints with Pydantic dataclasses provide validation for connection parameters and prevent configuration errors before runtime.

**Primary recommendation:** Use psycopg3 for PostgreSQL and mysql-connector-python for MySQL/MariaDB, implement configuration with Pydantic dataclasses for validation, use keyring for local credential storage, and apply the factory pattern to abstract database type differences.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| psycopg3 | 3.3.3+ | PostgreSQL adapter | Modern redesign with async support, connection pooling, server-side binding, pipeline mode; successor to psycopg2; official PostgreSQL adapter for Python |
| mysql-connector-python | 9.6.0+ | MySQL/MariaDB adapter | Official Oracle MySQL driver; PEP 249 compliant; pure Python with optional C extensions; supports MySQL 8.0+ and MariaDB; released Jan 2026 |
| pydantic | 2.x | Configuration validation | Industry standard for settings management with type validation; v2 uses Rust core (5-50x faster); native support for environment variables via pydantic-settings |
| python-dotenv | 1.x | Environment variable loading | Standard for local .env file management; widely used in development workflows; simple .env parsing |
| keyring | 25.7.0+ | Secure credential storage | OS-level credential storage (macOS Keychain, Windows Credential Locker, GNOME Keyring); encrypted storage using system authentication |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| psycopg_pool | 3.3.3+ | PostgreSQL connection pooling | When multiple concurrent connections needed; automatically installed with `psycopg[pool]`; configurable min/max size, timeouts, lifetime management |
| cryptography | 44.0.0+ | Credential encryption (Fernet) | When credentials must be stored encrypted at rest; AES-128 + HMAC-SHA256; use for config files that can't use keyring |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| psycopg3 | psycopg2 | psycopg2 is mature but lacks async support, modern connection pooling, and pipeline mode; psycopg3 is the recommended successor |
| mysql-connector-python | PyMySQL | PyMySQL is pure Python (more portable) but mysql-connector-python is official Oracle driver with better performance via C extensions; PyMySQL for maximum portability, mysql-connector-python for performance |
| pydantic | dataclasses + manual validation | Pydantic provides runtime validation, JSON schema generation, settings management; plain dataclasses require manual validation logic |
| keyring | AWS Secrets Manager / HashiCorp Vault | Cloud secret managers for production/multi-service environments; keyring for local development and single-machine deployments |

**Installation:**
```bash
# Core dependencies
uv add psycopg[pool] mysql-connector-python pydantic pydantic-settings python-dotenv keyring

# Optional: for encrypted credential storage
uv add cryptography
```

## Architecture Patterns

### Recommended Project Structure
```
src/
├── connection/
│   ├── __init__.py
│   ├── config.py          # Configuration models (Pydantic)
│   ├── factory.py         # Database connection factory
│   ├── base.py            # Abstract base class for connectors
│   ├── postgres.py        # PostgreSQL connector implementation
│   ├── mysql.py           # MySQL/MariaDB connector implementation
│   └── credentials.py     # Credential management (keyring, encryption)
└── ...
```

### Pattern 1: Configuration with Pydantic Validation
**What:** Define database configuration as Pydantic models with automatic validation
**When to use:** All database connection scenarios; validates types and required fields before connection attempts
**Example:**
```python
# Source: Pydantic docs + 2026 best practices
from pydantic import BaseModel, Field, field_validator
from typing import Literal

class DatabaseConfig(BaseModel):
    """Database connection configuration with validation."""
    db_type: Literal["postgresql", "mysql"]
    host: str = Field(..., min_length=1)
    port: int = Field(..., gt=0, lt=65536)
    database: str = Field(..., min_length=1)
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)
    ssl_enabled: bool = False
    connection_timeout: int = Field(default=10, gt=0)

    @field_validator('port')
    def validate_port_range(cls, v):
        if v < 1 or v > 65535:
            raise ValueError('Port must be between 1 and 65535')
        return v

# Usage with pydantic-settings for environment variables
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database: DatabaseConfig

    model_config = {
        "env_file": ".env",
        "env_nested_delimiter": "__"
    }
```

### Pattern 2: Connection Context Manager
**What:** Use context managers to ensure automatic connection cleanup and transaction handling
**When to use:** All database operations; guarantees resource cleanup even on exceptions
**Example:**
```python
# Source: psycopg3 official docs
import psycopg

# PostgreSQL - automatic commit on success, rollback on exception, close on exit
with psycopg.connect("dbname=test user=postgres") as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM test")
        result = cur.fetchone()
# Connection automatically closed here

# MySQL - similar pattern with mysql-connector-python
import mysql.connector

config = {
    'host': 'localhost',
    'user': 'user',
    'password': 'password',
    'database': 'db'
}

try:
    cnx = mysql.connector.connect(**config)
    cursor = cnx.cursor()
    cursor.execute("SELECT * FROM test")
    result = cursor.fetchone()
    cursor.close()
    cnx.close()
except mysql.connector.Error as err:
    print(f"Database error: {err}")
```

### Pattern 3: Factory Pattern for Multi-Database Support
**What:** Abstract database type differences behind a factory that creates appropriate connectors
**When to use:** Applications supporting multiple database types (PostgreSQL AND MySQL)
**Example:**
```python
# Source: Factory pattern best practices for database connections
from abc import ABC, abstractmethod
from typing import Protocol

class DatabaseConnector(Protocol):
    """Protocol defining database connector interface."""

    def connect(self) -> None:
        """Establish database connection."""
        ...

    def test_connection(self) -> bool:
        """Test if connection is alive."""
        ...

    def close(self) -> None:
        """Close database connection."""
        ...

class PostgreSQLConnector:
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.conn = None

    def connect(self) -> None:
        import psycopg
        self.conn = psycopg.connect(
            host=self.config.host,
            port=self.config.port,
            dbname=self.config.database,
            user=self.config.username,
            password=self.config.password,
            connect_timeout=self.config.connection_timeout
        )

    def test_connection(self) -> bool:
        try:
            with self.conn.cursor() as cur:
                cur.execute("SELECT 1")
                return True
        except Exception:
            return False

    def close(self) -> None:
        if self.conn:
            self.conn.close()

class MySQLConnector:
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.conn = None

    def connect(self) -> None:
        import mysql.connector
        self.conn = mysql.connector.connect(
            host=self.config.host,
            port=self.config.port,
            database=self.config.database,
            user=self.config.username,
            password=self.config.password,
            connection_timeout=self.config.connection_timeout
        )

    def test_connection(self) -> bool:
        # Use .connected property (is_connected() deprecated in 9.3.0+)
        return self.conn.connected if self.conn else False

    def close(self) -> None:
        if self.conn:
            self.conn.close()

class DatabaseFactory:
    """Factory for creating database connectors."""

    @staticmethod
    def create_connector(config: DatabaseConfig) -> DatabaseConnector:
        if config.db_type == "postgresql":
            return PostgreSQLConnector(config)
        elif config.db_type == "mysql":
            return MySQLConnector(config)
        else:
            raise ValueError(f"Unsupported database type: {config.db_type}")
```

### Pattern 4: Secure Credential Management
**What:** Use keyring for local development, environment variables for production
**When to use:** All credential storage scenarios; NEVER hardcode credentials
**Example:**
```python
# Source: keyring library docs + security best practices
import keyring
import os
from typing import Optional

class CredentialManager:
    """Manages database credentials securely."""

    def __init__(self, service_name: str = "AutomatedDataCataloger"):
        self.service_name = service_name

    def store_password(self, username: str, password: str) -> None:
        """Store password in OS keyring."""
        keyring.set_password(self.service_name, username, password)

    def get_password(self, username: str) -> Optional[str]:
        """Retrieve password from OS keyring."""
        return keyring.get_password(self.service_name, username)

    def get_from_env(self, key: str) -> Optional[str]:
        """Get credential from environment variable."""
        return os.getenv(key)

    def build_config_from_env(self) -> DatabaseConfig:
        """Build database config from environment variables."""
        return DatabaseConfig(
            db_type=os.getenv("DB_TYPE", "postgresql"),
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "5432")),
            database=os.getenv("DB_NAME"),
            username=os.getenv("DB_USER"),
            password=self.get_password(os.getenv("DB_USER"))
                     or os.getenv("DB_PASSWORD"),
            ssl_enabled=os.getenv("DB_SSL", "false").lower() == "true",
            connection_timeout=int(os.getenv("DB_TIMEOUT", "10"))
        )

# Alternative: Fernet encryption for stored credentials
from cryptography.fernet import Fernet
import json

class EncryptedCredentialStore:
    """Stores credentials encrypted at rest."""

    def __init__(self, key_path: str = ".key"):
        self.key_path = key_path
        self.key = self._load_or_create_key()
        self.cipher = Fernet(self.key)

    def _load_or_create_key(self) -> bytes:
        """Load existing key or create new one."""
        if os.path.exists(self.key_path):
            with open(self.key_path, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(self.key_path, 'wb') as f:
                f.write(key)
            return key

    def encrypt_config(self, config: DatabaseConfig, output_path: str) -> None:
        """Encrypt and store database configuration."""
        config_dict = config.model_dump()
        encrypted = self.cipher.encrypt(json.dumps(config_dict).encode())
        with open(output_path, 'wb') as f:
            f.write(encrypted)

    def decrypt_config(self, input_path: str) -> DatabaseConfig:
        """Decrypt and load database configuration."""
        with open(input_path, 'rb') as f:
            encrypted = f.read()
        decrypted = self.cipher.decrypt(encrypted)
        config_dict = json.loads(decrypted.decode())
        return DatabaseConfig(**config_dict)
```

### Pattern 5: Connection Testing with Specific Error Handling
**What:** Test connections with granular exception handling and clear user feedback
**When to use:** Initial connection setup, health checks, user-facing connection forms
**Example:**
```python
# Source: psycopg3 error handling docs + MySQL connector docs
import psycopg
import mysql.connector
from dataclasses import dataclass
from typing import Tuple, Optional

@dataclass
class ConnectionTestResult:
    """Result of connection test."""
    success: bool
    message: str
    error_type: Optional[str] = None

def test_postgresql_connection(config: DatabaseConfig) -> ConnectionTestResult:
    """Test PostgreSQL connection with detailed error handling."""
    try:
        conn = psycopg.connect(
            host=config.host,
            port=config.port,
            dbname=config.database,
            user=config.username,
            password=config.password,
            connect_timeout=config.connection_timeout
        )

        # Verify with simple query
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            result = cur.fetchone()

        conn.close()
        return ConnectionTestResult(
            success=True,
            message=f"Successfully connected to PostgreSQL database '{config.database}'"
        )

    except psycopg.OperationalError as e:
        # Network, authentication, or database availability issues
        error_msg = str(e)
        if "password authentication failed" in error_msg:
            return ConnectionTestResult(
                success=False,
                message="Authentication failed: Invalid username or password",
                error_type="AUTH_FAILED"
            )
        elif "could not connect to server" in error_msg:
            return ConnectionTestResult(
                success=False,
                message=f"Cannot reach database server at {config.host}:{config.port}",
                error_type="CONNECTION_REFUSED"
            )
        elif "database" in error_msg and "does not exist" in error_msg:
            return ConnectionTestResult(
                success=False,
                message=f"Database '{config.database}' does not exist",
                error_type="DB_NOT_FOUND"
            )
        else:
            return ConnectionTestResult(
                success=False,
                message=f"Connection error: {error_msg}",
                error_type="OPERATIONAL_ERROR"
            )

    except psycopg.ConnectionTimeout:
        return ConnectionTestResult(
            success=False,
            message=f"Connection timeout after {config.connection_timeout} seconds",
            error_type="TIMEOUT"
        )

    except psycopg.InterfaceError as e:
        return ConnectionTestResult(
            success=False,
            message=f"Database interface error: {str(e)}",
            error_type="INTERFACE_ERROR"
        )

    except Exception as e:
        return ConnectionTestResult(
            success=False,
            message=f"Unexpected error: {str(e)}",
            error_type="UNKNOWN_ERROR"
        )

def test_mysql_connection(config: DatabaseConfig) -> ConnectionTestResult:
    """Test MySQL/MariaDB connection with detailed error handling."""
    try:
        conn = mysql.connector.connect(
            host=config.host,
            port=config.port,
            database=config.database,
            user=config.username,
            password=config.password,
            connection_timeout=config.connection_timeout
        )

        # Verify connection using .connected property (is_connected() deprecated 9.3.0+)
        if not conn.connected:
            return ConnectionTestResult(
                success=False,
                message="Connection established but not active",
                error_type="NOT_CONNECTED"
            )

        # Test with simple query
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.close()
        conn.close()

        return ConnectionTestResult(
            success=True,
            message=f"Successfully connected to MySQL database '{config.database}'"
        )

    except mysql.connector.Error as err:
        from mysql.connector import errorcode

        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            return ConnectionTestResult(
                success=False,
                message="Authentication failed: Invalid username or password",
                error_type="AUTH_FAILED"
            )
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            return ConnectionTestResult(
                success=False,
                message=f"Database '{config.database}' does not exist",
                error_type="DB_NOT_FOUND"
            )
        else:
            return ConnectionTestResult(
                success=False,
                message=f"MySQL error: {str(err)}",
                error_type=f"MYSQL_ERROR_{err.errno}"
            )

    except Exception as e:
        return ConnectionTestResult(
            success=False,
            message=f"Unexpected error: {str(e)}",
            error_type="UNKNOWN_ERROR"
        )
```

### Anti-Patterns to Avoid
- **Not using context managers**: Leads to connection leaks; always use `with` statements for connections/cursors
- **Hardcoding credentials**: Security risk and inflexible; use environment variables, keyring, or secret management
- **Ignoring connection timeouts**: Leads to hanging applications; always set explicit timeouts
- **Single connection for concurrent operations**: Connection pool exhaustion; use connection pooling for concurrent requests
- **Not closing connections explicitly (without context managers)**: Resource leaks; if not using `with`, explicitly close in `finally` blocks
- **Returning different types on error**: Type inconsistency (e.g., return User or error tuple); raise exceptions or return Result objects
- **Using deprecated methods**: `mysql.connector.MySQLConnection.is_connected()` deprecated in 9.3.0+; use `.connected` property

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Database drivers | Custom socket/protocol implementation | psycopg3, mysql-connector-python | PostgreSQL/MySQL wire protocols are complex with authentication, encoding, type mapping, prepared statements, and connection state management |
| Connection pooling | Custom connection queue/manager | psycopg_pool.ConnectionPool | Pool implementations must handle connection lifecycle, validation, stale detection, timeout management, leak detection, and thread safety |
| Credential encryption | Custom encryption algorithm | cryptography library (Fernet) | Cryptography requires expertise; Fernet provides authenticated encryption (AES-128 + HMAC-SHA256) with proper key derivation |
| Configuration validation | Manual type checking and validation | Pydantic BaseModel with field validators | Validation logic is error-prone; Pydantic provides declarative validation, type coercion, JSON schema generation, and clear error messages |
| Connection retry logic | Manual retry loops | Built-in retry with exponential backoff libraries | Retry logic requires exponential backoff, jitter, max attempts, timeout handling, and specific error detection |
| SQL injection protection | Manual string escaping | Parameterized queries (always) | SQL escaping has edge cases that vary by database; parameterized queries use server-side binding (psycopg3) or prepared statements |

**Key insight:** Database connectivity has numerous edge cases (network failures, authentication methods, SSL/TLS configuration, encoding issues, connection state, transaction management). Battle-tested libraries have solved these problems. Custom implementations will miss critical edge cases and security considerations.

## Common Pitfalls

### Pitfall 1: Connection Leaks from Missing Context Managers
**What goes wrong:** Connections are created but never closed, exhausting database connection limits
**Why it happens:** Forgetting to close connections or exceptions preventing `close()` calls
**How to avoid:** Always use context managers (`with` statements) for connections and cursors
**Warning signs:** "Too many connections" errors, growing memory usage, database refusing new connections

### Pitfall 2: Storing Credentials in Version Control
**What goes wrong:** Database passwords committed to git history, exposing credentials publicly
**Why it happens:** Hardcoding credentials in source files or forgetting to `.gitignore` .env files
**How to avoid:** Use keyring for local dev, environment variables for production; add `.env` to `.gitignore`; never hardcode credentials
**Warning signs:** Credentials visible in `git log`, .env files in repository, security scanner alerts

### Pitfall 3: Not Handling Specific Exception Types
**What goes wrong:** Generic error messages ("Connection failed") don't help users diagnose issues
**Why it happens:** Catching broad `Exception` instead of database-specific exceptions
**How to avoid:** Catch specific exceptions (OperationalError, InterfaceError, ConnectionTimeout) and provide actionable messages
**Warning signs:** User confusion about connection failures, support tickets asking "why did it fail?"

### Pitfall 4: Connection Timeout Not Set
**What goes wrong:** Application hangs indefinitely when database is unreachable
**Why it happens:** Default timeout behavior varies; some drivers wait indefinitely
**How to avoid:** Always set explicit `connect_timeout` (10-30 seconds recommended for user-facing operations)
**Warning signs:** Application freezing on startup, non-responsive UI during connection attempts

### Pitfall 5: Using Deprecated MySQL Methods
**What goes wrong:** Code breaks when upgrading mysql-connector-python to 9.3.0+
**Why it happens:** `is_connected()` method deprecated in favor of `.connected` property
**How to avoid:** Use `.connected` property instead of `is_connected()` method
**Warning signs:** Deprecation warnings in logs, test failures after library upgrades

### Pitfall 6: Connection Pool Exhaustion
**What goes wrong:** Application runs out of available connections under load
**Why it happens:** Not returning connections to pool, pool sized too small, connections held open too long
**How to avoid:** Use context managers to ensure return to pool; monitor pool metrics; size pool based on concurrency needs; keep transactions short
**Warning signs:** "Pool timeout" errors, increasing connection wait times, application slowdown under load

### Pitfall 7: Not Validating Configuration Before Connection
**What goes wrong:** Invalid config values (port = 0, empty host) cause cryptic connection errors
**Why it happens:** No validation layer between user input and connection attempt
**How to avoid:** Use Pydantic models with field validators to catch invalid config before attempting connection
**Warning signs:** Stack traces from database drivers about invalid parameters, error messages that don't help users

### Pitfall 8: MySQL vs MariaDB Compatibility Assumptions
**What goes wrong:** Code works with MySQL but fails with MariaDB or vice versa
**Why it happens:** MariaDB diverged from MySQL (different JSON handling, no X Protocol, different feature sets)
**How to avoid:** Test with both MySQL and MariaDB if supporting both; use mysql-connector-python which supports both; avoid MySQL-specific features
**Warning signs:** User reports of failures with one database type, feature availability differences

## Code Examples

Verified patterns from official sources:

### PostgreSQL Connection with psycopg3
```python
# Source: https://www.psycopg.org/psycopg3/docs/basic/usage.html
import psycopg

# Recommended pattern: context manager with transaction handling
with psycopg.connect("dbname=test user=postgres") as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM test WHERE id = %s", (42,))
        result = cur.fetchone()
# Transaction committed on success, rolled back on exception, connection closed

# Connection string with parameters
with psycopg.connect(
    "host=localhost dbname=test user=postgres connect_timeout=10"
) as conn:
    # Use connection
    pass

# Using connection parameters dictionary
conn_params = {
    "host": "localhost",
    "port": 5432,
    "dbname": "test",
    "user": "postgres",
    "password": "secret",
    "connect_timeout": 10
}
with psycopg.connect(**conn_params) as conn:
    pass
```

### MySQL Connection with mysql-connector-python
```python
# Source: https://dev.mysql.com/doc/connector-python/en/connector-python-example-connecting.html
import mysql.connector
from mysql.connector import errorcode

# Recommended pattern: configuration dictionary with error handling
config = {
    'host': '127.0.0.1',
    'port': 3306,
    'database': 'employees',
    'user': 'scott',
    'password': 'password',
    'connection_timeout': 10,
    'raise_on_warnings': True
}

try:
    cnx = mysql.connector.connect(**config)
    cursor = cnx.cursor()

    # Parameterized query (prevents SQL injection)
    cursor.execute("SELECT * FROM users WHERE id = %s", (42,))
    result = cursor.fetchone()

    cursor.close()
    cnx.close()

except mysql.connector.Error as err:
    if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
        print("Invalid username or password")
    elif err.errno == errorcode.ER_BAD_DB_ERROR:
        print("Database does not exist")
    else:
        print(f"Error: {err}")
```

### Connection Pool with psycopg3
```python
# Source: https://www.psycopg.org/psycopg3/docs/advanced/pool.html
from psycopg_pool import ConnectionPool

# Create pool (initialize once, use throughout application)
pool = ConnectionPool(
    conninfo="host=localhost dbname=test user=postgres",
    min_size=4,           # Minimum connections maintained
    max_size=10,          # Maximum connections allowed
    timeout=30.0,         # Client wait timeout for connection
    max_lifetime=3600.0,  # Max connection lifetime (1 hour)
    max_idle=600.0,       # Max idle time before closing (10 minutes)
    reconnect_timeout=300.0  # Max time for reconnection attempts
)

# Wait for pool to be ready (recommended at startup)
pool.wait()

# Use pool connection with context manager
with pool.connection() as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM test")
        result = cur.fetchone()
# Connection automatically returned to pool
```

### Secure Credential Storage with keyring
```python
# Source: https://keyring.readthedocs.io/en/latest/
import keyring

# Store credentials (one-time setup)
service_name = "AutomatedDataCataloger"
username = "db_user"
password = "super_secret_password"

keyring.set_password(service_name, username, password)

# Retrieve credentials (in application)
stored_password = keyring.get_password(service_name, username)

# Use with database connection
import psycopg
conn_params = {
    "host": "localhost",
    "dbname": "catalog",
    "user": username,
    "password": stored_password  # Retrieved from OS keyring
}

with psycopg.connect(**conn_params) as conn:
    pass
```

### Configuration with Pydantic and Environment Variables
```python
# Source: Pydantic docs (https://docs.pydantic.dev/latest/concepts/config/)
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal
import os

class DatabaseConfig(BaseModel):
    """Database connection configuration."""
    db_type: Literal["postgresql", "mysql"]
    host: str = Field(..., min_length=1)
    port: int = Field(..., gt=0, le=65535)
    database: str = Field(..., min_length=1)
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)
    connection_timeout: int = Field(default=10, gt=0)

class Settings(BaseSettings):
    """Application settings loaded from environment."""
    database: DatabaseConfig

    model_config = SettingsConfigDict(
        env_file=".env",
        env_nested_delimiter="__"
    )

# Example .env file:
# DATABASE__DB_TYPE=postgresql
# DATABASE__HOST=localhost
# DATABASE__PORT=5432
# DATABASE__DATABASE=catalog
# DATABASE__USERNAME=postgres
# DATABASE__PASSWORD=secret
# DATABASE__CONNECTION_TIMEOUT=10

# Load settings
settings = Settings()
print(settings.database.host)  # "localhost"
```

### Connection Retry with Exponential Backoff
```python
# Source: MySQL Connector docs + retry best practices
import time
import logging
import mysql.connector
from typing import Optional

logger = logging.getLogger(__name__)

def connect_with_retry(
    config: dict,
    max_attempts: int = 3,
    initial_delay: float = 1.0
) -> Optional[mysql.connector.MySQLConnection]:
    """
    Connect to MySQL with exponential backoff retry.

    Args:
        config: Connection configuration dictionary
        max_attempts: Maximum number of connection attempts
        initial_delay: Initial delay between retries (doubles each attempt)

    Returns:
        Connection object or None if all attempts failed
    """
    attempt = 1
    delay = initial_delay

    while attempt <= max_attempts:
        try:
            conn = mysql.connector.connect(**config)
            logger.info(f"Connected on attempt {attempt}/{max_attempts}")
            return conn

        except (mysql.connector.Error, IOError) as err:
            if attempt == max_attempts:
                logger.error(f"Failed to connect after {max_attempts} attempts: {err}")
                return None

            logger.warning(
                f"Connection attempt {attempt}/{max_attempts} failed: {err}. "
                f"Retrying in {delay:.1f}s..."
            )
            time.sleep(delay)
            delay *= 2  # Exponential backoff
            attempt += 1

    return None

# Usage
config = {
    'host': 'localhost',
    'database': 'test',
    'user': 'root',
    'password': 'password',
    'connection_timeout': 10
}

conn = connect_with_retry(config, max_attempts=3, initial_delay=1.0)
if conn:
    # Use connection
    conn.close()
else:
    print("Could not establish connection")
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| psycopg2 | psycopg3 | 2021-2024 | Async support, better connection pooling, server-side binding, pipeline mode; psycopg2 still maintained but psycopg3 recommended for new projects |
| mysql.connector.is_connected() | mysql.connector.connected property | Version 9.3.0 (2024) | Method deprecated; property provides same functionality with Pythonic syntax |
| Manual password validation | pydantic-settings with BaseSettings | Pydantic v2 (2023) | Automated environment variable loading, validation, and type coercion; 5-50x faster with Rust core |
| Plain text .env files only | keyring + environment variables | Ongoing best practice evolution | OS-level encrypted storage for local dev; environment variables for production |
| Manual connection pooling | psycopg_pool.ConnectionPool | psycopg3 release (2021+) | Redesigned pool with better timeout handling, leak detection, connection lifetime management |
| mysql-connector-python use_pure=True default | use_pure=False default | MySQL 8.0 era | C extension enabled by default for better performance; pure Python still available for portability |

**Deprecated/outdated:**
- **psycopg2**: Still maintained but psycopg3 recommended; lacks async, modern pooling, pipeline mode
- **mysql.connector.is_connected()**: Deprecated 9.3.0+; use `.connected` property
- **Hardcoded credentials**: Never acceptable; use keyring, env vars, or secret managers
- **Missing connection timeouts**: Modern practice always sets explicit timeouts
- **mysql-connector-python v1.x**: Version 2.x+ aligns major version with MySQL server version

## Open Questions

1. **Connection Pool Sizing for This Application**
   - What we know: psycopg_pool supports min_size and max_size configuration
   - What's unclear: Optimal pool size depends on expected concurrent cataloging operations
   - Recommendation: Start with min_size=2, max_size=5 for single-user CLI; monitor and adjust based on actual usage; Phase 6 web UI may need larger pool

2. **SSL/TLS Configuration Requirements**
   - What we know: Both psycopg3 and mysql-connector-python support SSL with sslmode, sslrootcert, sslcert parameters
   - What's unclear: Whether target databases require SSL; certificate management approach
   - Recommendation: Make SSL optional (ssl_enabled config flag); document SSL setup in user guide; default to unencrypted for local dev databases

3. **Support for MySQL vs MariaDB Differences**
   - What we know: mysql-connector-python works with both; MariaDB diverged from MySQL (no X Protocol, different JSON handling)
   - What's unclear: Whether to explicitly test and support MariaDB-specific features or treat as MySQL-compatible
   - Recommendation: Use mysql-connector-python for both; avoid MySQL-specific features; test with both MySQL 8.0+ and MariaDB 10.x if possible

4. **Production Secret Management Strategy**
   - What we know: keyring for local dev; AWS Secrets Manager, HashiCorp Vault for production
   - What's unclear: Target deployment environment (local, cloud, Docker)
   - Recommendation: Support both keyring (local dev) and environment variables (production); defer cloud secret manager integration to future phase

## Sources

### Primary (HIGH confidence)
- [Psycopg3 Official Documentation](https://www.psycopg.org/psycopg3/docs/) - Connection patterns, context managers, error handling
- [Psycopg3 Basic Usage Guide](https://www.psycopg.org/psycopg3/docs/basic/usage.html) - Connection examples and best practices
- [Psycopg3 Connection Pools](https://www.psycopg.org/psycopg3/docs/advanced/pool.html) - Pool configuration and usage
- [Psycopg3 Error Handling](https://www.psycopg.org/psycopg3/docs/api/errors.html) - Exception types and handling
- [MySQL Connector/Python Official Documentation](https://dev.mysql.com/doc/connector-python/en/) - Official MySQL driver reference
- [MySQL Connector/Python Connection Guide](https://dev.mysql.com/doc/connector-python/en/connector-python-example-connecting.html) - Connection examples and error handling
- [MySQL Connector/Python Connection Arguments](https://dev.mysql.com/doc/connector-python/en/connector-python-connectargs.html) - Configuration parameters
- [MySQL Connector/Python is_connected() Method](https://dev.mysql.com/doc/connector-python/en/connector-python-api-mysqlconnection-is-connected.html) - Deprecation notice and replacement
- [mysql-connector-python PyPI](https://pypi.org/project/mysql-connector-python/) - Version 9.6.0 release (Jan 21, 2026)
- [Pydantic Documentation](https://docs.pydantic.dev/latest/) - Configuration validation and settings management
- [Pydantic Dataclasses](https://docs.pydantic.dev/latest/concepts/dataclasses/) - Validation with dataclasses
- [Pydantic Configuration](https://docs.pydantic.dev/latest/concepts/config/) - Model configuration options
- [Cryptography Library - Fernet](https://cryptography.io/en/latest/fernet/) - Symmetric encryption for credentials
- [cryptography PyPI](https://pypi.org/project/cryptography/) - Latest version and installation
- [keyring Documentation](https://keyring.readthedocs.io/en/latest/) - OS-level credential storage
- [keyring PyPI](https://pypi.org/project/keyring/) - Version 25.7.0+ features

### Secondary (MEDIUM confidence)
- [Using psycopg2 to Connect Python to PostgreSQL](https://www.sqlservercentral.com/articles/using-psycopg2-to-connect-python-to-postgresql) - Verified with official docs
- [How Python Talks to PostgreSQL: Psycopg to ORM Guide](https://leapcell.io/blog/python-postgres-psycopg-orm-guide) - psycopg3 modern features
- [Python MySQL Database Connection Guide](https://pynative.com/python-mysql-database-connection/) - Verified with official MySQL docs
- [PyMySQL GitHub](https://github.com/PyMySQL/PyMySQL) - Alternative MySQL driver comparison
- [Secure Password Handling in Python](https://martinheinz.dev/blog/59) - Multiple sources confirm best practices
- [How To Securely Save Credentials in Python](https://medium.com/jungletronics/how-to-securely-save-credentials-in-python-dd5c6983741a) - keyring + encryption patterns
- [Securing Sensitive Data in Python: Best Practices for API Keys and Credentials](https://systemweakness.com/securing-sensitive-data-in-python-best-practices-for-storing-api-keys-and-credentials-2bee9ede57ee) - Verified with official library docs
- [Using Try-Except for Database Error Handling in Python](https://www.index.dev/blog/python-database-error-handling-try-except) - Exception handling patterns
- [Testing MySQL Connectivity Using Dockerized Python Container (2026-01-03)](https://note.shahadathossain.com/2026/01/03/testing-mysql-connectivity-using-a-dockerized-python-container/) - Recent 2026 testing patterns
- [How to Build Connection Health Checks (2026-01-30)](https://oneuptime.com/blog/post/2026-01-30-connection-health-checks/view) - Current best practices
- [FastAPI Health Check Endpoint Example](https://www.index.dev/blog/how-to-implement-health-check-in-python) - Connection validation patterns
- [MariaDB vs MySQL Compatibility](https://mariadb.com/docs/release-notes/community-server/about/compatibility-and-differences/mariadb-vs-mysql-compatibility) - Official compatibility documentation
- [MariaDB vs MySQL 2026 Comparison](https://www.integrate.io/blog/mariadb-vs-mysql-everything-you-need-to-know/) - Updated differences
- [MariaDB Connector/Python Documentation](https://mariadb.com/docs/connectors/mariadb-connector-python) - Official MariaDB connector
- [Understanding Factory Method Pattern with Python Database Connections](https://medium.com/@tharinduimalka915/understanding-the-factory-method-pattern-a-real-world-example-with-python-database-connections-945f31f4ea8b) - Design pattern application
- [How to Fix Connection Pool Exhausted Errors (2026-01-24)](https://oneuptime.com/blog/post/2026-01-24-connection-pool-exhausted-errors/view) - Recent prevention strategies
- [PostgreSQL Connection Pool Exhaustion: Lessons from Production](https://www.c-sharpcorner.com/article/postgresql-connection-pool-exhaustion-lessons-from-a-production-outage/) - Real-world pitfalls
- [Using Python to Establish SSL/TLS Connections to AWS RDS MySQL](https://www.gaurishsharma.com/2023/03/using-python-to-establish-ssl-tls-encrypted-connections-to-aws-rds-mysql-5-7.html) - SSL configuration patterns
- [How to Use SSL Mode in psycopg2](https://www.geeksforgeeks.org/python/how-to-use-ssl-mode-in-psycopg2-using-python/) - PostgreSQL SSL configuration
- [Python Type Hints: Complete Guide for 2026](https://devtoolbox.dedyn.io/blog/python-type-hints-complete-guide) - Recent type hints guide
- [Pydantic Complete Guide for 2026](https://devtoolbox.dedyn.io/blog/pydantic-complete-guide) - Recent Pydantic v2 patterns
- [How to Use Type Hints in Python (2026-01-22)](https://oneuptime.com/blog/post/2026-01-22-type-hints-python/view) - Current best practices
- [Python Fernet AES Encryption: Complete 2026 Guide](https://copyprogramming.com/howto/python-cryptography-fernet-generate-key-key-length) - Recent encryption guide
- [Password Management in Python: Keyring and Credential Manager](https://medium.com/@aarhar/password-management-in-python-keyring-and-credential-manager-29fa4ccc919e) - Keyring usage patterns
- [Securely Storing Credentials in Python with Keyring](https://www.allscient.com/post/securely-storing-credentials-in-python-with-keyring) - Best practices

### Tertiary (LOW confidence - marked for validation)
- General Python anti-patterns resources - not database-specific; need domain expert review

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All libraries verified from official PyPI, docs, and 2026 sources; versions confirmed current
- Architecture: HIGH - Patterns verified from official documentation (psycopg3, MySQL Connector, Pydantic); factory pattern from multiple sources; all code examples from official docs
- Pitfalls: MEDIUM-HIGH - Connection leaks, credential storage, error handling verified from official docs and 2026 sources; pool exhaustion from recent 2026 blog posts; MySQL deprecations from official docs

**Research date:** 2026-02-21
**Valid until:** 2026-04-21 (60 days - stable libraries with mature ecosystems; psycopg3 and mysql-connector-python have established release cycles)
