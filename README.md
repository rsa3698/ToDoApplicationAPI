# ToDoApp - A FastAPI-Powered Task Management Application

## Project Description

ToDoApp is a backend application designed to help users manage their tasks. It provides API endpoints for creating, reading, updating, and deleting tasks (todos). The application also includes user authentication, allowing users to register, log in, and manage their own tasks securely.

## Application Architecture

The ToDoApp is built using a modern Python stack, leveraging several powerful libraries and tools:

-   **FastAPI:** A modern, fast (high-performance), web framework for building APIs with Python based on standard Python type hints. It handles incoming HTTP requests, routing, request validation, and response serialization.
-   **SQLAlchemy:** A SQL toolkit and Object-Relational Mapper (ORM) that gives application developers the full power and flexibility of SQL. It's used to define database models (e.g., Users, Todos) and interact with the database.
-   **Pydantic:** Used for data validation and settings management using Python type annotations. FastAPI uses Pydantic models to define request and response bodies, ensuring data consistency and providing automatic validation.
-   **PostgreSQL:** A powerful, open-source object-relational database system. It serves as the primary data store for the application, persisting user information and todo items. (Note: The application is configured for PostgreSQL, but SQLAlchemy allows for other database backends as well).
-   **Alembic:** A lightweight database migration tool for SQLAlchemy. It allows for managing and applying changes to the database schema over time as the application evolves. Migrations are written as Python scripts.
-   **Passlib & python-jose:** Used for security aspects, specifically password hashing (`passlib` with `bcrypt`) and JWT-based authentication token generation and verification (`python-jose`).

**Interaction Flow:**

1.  **HTTP Request:** A client sends an HTTP request to a specific API endpoint.
2.  **FastAPI:** Receives the request, validates path and query parameters, and (if applicable) the request body using Pydantic models.
3.  **Router:** The request is directed to the appropriate path operation function within a router (e.g., `todos.py`, `auth.py`).
4.  **Dependencies (Authentication & DB Session):**
    *   Authentication (`get_current_user`): If the endpoint requires authentication, a dependency verifies the JWT token from the request headers.
    *   Database Session (`get_db`): A SQLAlchemy database session is created and provided to the path operation function.
5.  **Business Logic:** The path operation function executes the core logic:
    *   **Models:** Interacts with SQLAlchemy models (`Users`, `Todos`) which represent database tables.
    *   **Database Interaction:** Uses the SQLAlchemy session to query the database (e.g., create, retrieve, update, delete records).
6.  **Pydantic (Response Model):** The result of the operation is often passed through a Pydantic response model to serialize it into a JSON response.
7.  **FastAPI:** Sends the HTTP response (e.g., JSON data, status code) back to the client.

## Code Flow

A typical request-response cycle in ToDoApp follows these steps:

1.  **Client Request:** A user or frontend application sends an HTTP request (e.g., `POST /todos/` to create a new todo) to the FastAPI application.
2.  **FastAPI Routing:** FastAPI receives the request. Based on the URL path and HTTP method, it routes the request to the corresponding path operation function defined in one of the router files (e.g., `ToDoApp/routers/todos.py`).
3.  **Dependency Injection:**
    *   **Authentication:** If the route is protected, the `get_current_user` dependency (from `ToDoApp/routers/auth.py`) is invoked. This function expects a JWT token in the `Authorization` header, decodes it, and returns the current user's information. If authentication fails, an HTTP exception is raised.
    *   **Database Session:** The `get_db` dependency (defined in each router, e.g., `ToDoApp/routers/todos.py`) provides a SQLAlchemy database session (`SessionLocal` from `ToDoApp/database.py`) for the current request. This session is used for all database operations within that request and is closed after the request is complete.
4.  **Request Validation (Pydantic):** If the request includes a body (e.g., for creating or updating a todo), FastAPI uses the Pydantic model specified in the type hints (e.g., `TodoRequest` in `ToDoApp/routers/todos.py`) to validate the incoming JSON data. If validation fails, FastAPI automatically returns a 422 Unprocessable Entity error with details.
5.  **Path Operation Function Execution:**
    *   The router function (e.g., `create_todo` in `ToDoApp/routers/todos.py`) is executed.
    *   It uses the injected database session (`db`) to interact with the database via SQLAlchemy models (e.g., `models.Todos`). This might involve creating new model instances, querying existing records, updating, or deleting them.
    *   For example, `db.add(todo_model)` stages a new record, and `db.commit()` saves it to the database. `db.query(models.Todos).filter(...).first()` retrieves records.
6.  **Response Generation:**
    *   The path operation function typically returns data (e.g., a SQLAlchemy model instance or a list of them).
    *   FastAPI uses the `response_model` (if defined for the path operation) to serialize the returned data into a JSON response, filtering out any fields not defined in the response model.
    *   The appropriate HTTP status code is set (e.g., `201 Created`, `200 OK`).
7.  **Client Receives Response:** The JSON response and status code are sent back to the client.

## Steps to Run the Project

### 1. Development Environment Setup

*   **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd ToDoAppProject # Or your project's root directory
    ```
*   **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
*   **Database Setup (PostgreSQL):**
    *   Ensure you have PostgreSQL installed and running.
    *   Create a database for the project, e.g., `ToDoApplicationDatabase`.
    *   Update the database connection string in `ToDoApp/database.py` if your PostgreSQL setup is different:
        ```python
        POSTGRESQL_DATABASE_URL = "postgresql://username:password@host:port/database_name"
        ```
        (The current default is `postgresql://postgres:1234@localhost/ToDoApplicationDatabase`)

### 2. Install Dependencies

*   Install the required Python packages:
    ```bash
    pip install fastapi uvicorn sqlalchemy pydantic psycopg2-binary passlib python-jose[cryptography] alembic bcrypt python-multipart pytest pytest-html pytest-cov
    ```
    (Note: `psycopg2-binary` is for PostgreSQL connection. If you use a different DB, install its driver. `pytest`, `pytest-html`, and `pytest-cov` are for running tests and generating reports.)

### 3. Database Migrations (Alembic)

*   **Initialize Alembic (if not already done in the project - it appears to be set up):**
    The project already contains an `alembic.ini` and an `alembic` directory, so initialization is likely done. The `env.py` file within the `alembic` directory is configured to use the `POSTGRESQL_DATABASE_URL` from `ToDoApp.database`.
*   **Create a new migration (if you make changes to SQLAlchemy models in `ToDoApp/models.py`):**
    ```bash
    alembic revision -m "description_of_your_changes"
    ```
    This will generate a new migration script in `ToDoApp/alembic/versions/`. Review and edit this script as needed.
*   **Apply migrations to the database:**
    ```bash
    alembic upgrade head
    ```
    This will apply all pending migrations to your database, creating or updating tables according to your models.

### 4. Start the Application

*   Run the FastAPI application using Uvicorn:
    ```bash
    uvicorn ToDoApp.main:app --reload
    ```
    *   `ToDoApp.main:app` refers to the `app` instance of `FastAPI` in the `ToDoApp/main.py` file.
    *   `--reload` enables auto-reloading when code changes, which is useful for development.
*   The application will typically be available at `http://127.0.0.1:8000`.
*   You can access the API documentation (Swagger UI) at `http://127.0.0.1:8000/docs` and ReDoc at `http://127.0.0.1:8000/redoc`.

### 5. Running Tests

*   Ensure you have `pytest` installed (it's included in the `pip install` command above).
*   Navigate to the project's root directory (e.g., `/app` in the sandbox environment, or the directory containing `ToDoApp`).
*   Run pytest:
    ```bash
    pytest
    ```
    Or to run tests for a specific file:
    ```bash
    pytest ToDoApp/tests/test_todos.py
    pytest ToDoApp/tests/test_auth.py
    ```
*   **Generating HTML Test Reports and Coverage Reports:**
    To generate a self-contained HTML test report and a code coverage report, run:
    ```bash
    pytest --html=pytest_report.html --self-contained-html --cov=ToDoApp --cov-report=html
    ```
    *   The HTML test report will be saved as `pytest_report.html` in the root directory.
    *   The code coverage report will be generated in the `htmlcov/` directory. Open `htmlcov/index.html` in your browser to view it.

This README provides a comprehensive guide to understanding, running, and testing the ToDoApp application.
