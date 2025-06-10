import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from ToDoApp.main import app
from ToDoApp.routers.todos import get_db # Corrected import for get_db
from ToDoApp.routers.auth import get_current_user
from ToDoApp.models import Todos, Users

# Mock database session
class MockSession:
    def __init__(self):
        self.data = {}
        self.commit_count = 0
        self.rollback_count = 0
        self.refresh_count = 0
        self.add_count = 0
        self.query_count = 0
        self.filter_count = 0
        self.first_count = 0
        self.delete_count = 0
        self._next_id = 1

    def query(self, model):
        self.query_count += 1
        # Return a query object that can be filtered
        class Query:
            def __init__(self, data, model_cls):
                self._data = data
                self._model_cls = model_cls
                self.first_called = False
                self.all_called = False

            def filter(self, *conditions):
                current_items = list(self._data.get(self._model_cls, [])) # Make a mutable copy

                for condition in conditions:
                    attr_name = condition.left.name
                    value = condition.right.value

                    # Apply this condition to the current_items
                    if self._model_cls == Todos and attr_name == "owner_id":
                        current_items = [
                            item for item in current_items
                            if getattr(item, attr_name, None) == value
                        ]
                    elif self._model_cls == Todos and attr_name == "id":
                        current_items = [
                            item for item in current_items
                            if getattr(item, attr_name, None) == value
                        ]
                    else:
                        # Generic filter (may need adjustment for specific test cases)
                        current_items = [
                            item for item in current_items
                            if getattr(item, attr_name, None) == value
                        ]

                # Return a new Query object with the finally filtered data
                new_query = Query(self._data, self._model_cls) # Pass original _data for further queries if needed
                new_query._data = {self._model_cls: current_items} # Store filtered items
                return new_query


            def first(self):
                self.first_called = True
                items = self._data.get(self._model_cls, [])
                return items[0] if items else None

            def all(self):
                self.all_called = True
                return self._data.get(self._model_cls, [])


        return Query(self.data, model)

    def add(self, instance):
        self.add_count += 1
        model_type = type(instance)
        if model_type not in self.data:
            self.data[model_type] = []

        # Assign an ID if it's a Todo model and doesn't have one
        if isinstance(instance, Todos) and not instance.id:
            instance.id = self._next_id
            self._next_id += 1

        self.data[model_type].append(instance)

    def commit(self):
        self.commit_count += 1

    def rollback(self):
        self.rollback_count += 1

    def refresh(self, instance):
        self.refresh_count += 1

    def delete(self, instance):
        self.delete_count += 1
        model_type = type(instance)
        if model_type in self.data and instance in self.data[model_type]:
            self.data[model_type].remove(instance)

    def close(self):
        pass


@pytest.fixture
def mock_db_session():
    return MockSession()

@pytest.fixture
def test_user():
    return Users(id=1, username="testuser", email="test@example.com", hashed_password="hashedpassword", role="user")

# Override dependencies
def override_get_db():
    db = MockSession()
    try:
        yield db
    finally:
        db.close()

def override_get_current_user():
    return {"id": 1, "username": "testuser", "role": "user"}

app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user

client = TestClient(app)

# --- Test Cases ---

def test_create_todo(mock_db_session: MockSession, test_user: Users):
    # Override get_db for this specific test
    app.dependency_overrides[get_db] = lambda: mock_db_session
    app.dependency_overrides[get_current_user] = lambda: {"id": test_user.id, "username": test_user.username, "role": test_user.role}


    response = client.post(
        "/todos/",
        json={"title": "Test Todo", "description": "Test Description", "priority": 1, "complete": False}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Todo"
    assert data["owner_id"] == test_user.id

    # Verify data in mock_db_session
    assert len(mock_db_session.data.get(Todos, [])) == 1
    created_todo = mock_db_session.data[Todos][0]
    assert created_todo.title == "Test Todo"
    assert created_todo.owner_id == test_user.id


def test_read_all_todos(mock_db_session: MockSession, test_user: Users):
    app.dependency_overrides[get_db] = lambda: mock_db_session
    app.dependency_overrides[get_current_user] = lambda: {"id": test_user.id, "username": test_user.username, "role": test_user.role}

    # Add some todos to the mock database
    todo1 = Todos(title="Todo 1", description="Desc 1", priority=1, complete=False, owner_id=test_user.id)
    todo2 = Todos(title="Todo 2", description="Desc 2", priority=2, complete=True, owner_id=test_user.id)
    mock_db_session.add(todo1)
    mock_db_session.add(todo2)
    mock_db_session.commit()

    response = client.get("/todos/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["title"] == "Todo 1"
    assert data[1]["title"] == "Todo 2"


def test_read_todo_by_id_success(mock_db_session: MockSession, test_user: Users):
    app.dependency_overrides[get_db] = lambda: mock_db_session
    app.dependency_overrides[get_current_user] = lambda: {"id": test_user.id, "username": test_user.username, "role": test_user.role}

    todo = Todos(id=1, title="Specific Todo", description="Desc", priority=1, complete=False, owner_id=test_user.id)
    mock_db_session.add(todo)
    mock_db_session.commit()

    response = client.get(f"/todos/{todo.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Specific Todo"
    assert data["id"] == todo.id


def test_read_todo_by_id_not_found(mock_db_session: MockSession, test_user: Users):
    app.dependency_overrides[get_db] = lambda: mock_db_session
    app.dependency_overrides[get_current_user] = lambda: {"id": test_user.id, "username": test_user.username, "role": test_user.role}

    response = client.get("/todos/999")  # Non-existent ID
    assert response.status_code == 404
    assert response.json() == {"detail": "Todo not found"}


def test_update_todo_success(mock_db_session: MockSession, test_user: Users):
    app.dependency_overrides[get_db] = lambda: mock_db_session
    app.dependency_overrides[get_current_user] = lambda: {"id": test_user.id, "username": test_user.username, "role": test_user.role}

    todo = Todos(id=1, title="Old Title", description="Old Desc", priority=1, complete=False, owner_id=test_user.id)
    mock_db_session.add(todo)
    mock_db_session.commit()

    updated_data = {"title": "New Title", "description": "New Desc", "priority": 2, "complete": True}
    response = client.put(f"/todos/{todo.id}", json=updated_data)

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "New Title"
    assert data["priority"] == 2
    assert data["complete"] is True

    # Verify update in mock_db
    updated_todo_in_db = mock_db_session.query(Todos).filter(Todos.id == todo.id).first()
    assert updated_todo_in_db is not None
    assert updated_todo_in_db.title == "New Title"


def test_update_todo_not_found(mock_db_session: MockSession, test_user: Users):
    app.dependency_overrides[get_db] = lambda: mock_db_session
    app.dependency_overrides[get_current_user] = lambda: {"id": test_user.id, "username": test_user.username, "role": test_user.role}

    updated_data = {"title": "New Title", "description": "New Desc", "priority": 2, "complete": True}
    response = client.put("/todos/999", json=updated_data)  # Non-existent ID

    assert response.status_code == 404
    assert response.json() == {"detail": "Todo not found"}


def test_delete_todo_success(mock_db_session: MockSession, test_user: Users):
    app.dependency_overrides[get_db] = lambda: mock_db_session
    app.dependency_overrides[get_current_user] = lambda: {"id": test_user.id, "username": test_user.username, "role": test_user.role}

    todo = Todos(id=1, title="To Be Deleted", description="Desc", priority=1, complete=False, owner_id=test_user.id)
    mock_db_session.add(todo)
    mock_db_session.commit()

    response = client.delete(f"/todos/{todo.id}")
    assert response.status_code == 204

    # Verify deletion in mock_db
    deleted_todo_in_db = mock_db_session.query(Todos).filter(Todos.id == todo.id).first()
    assert deleted_todo_in_db is None


def test_delete_todo_not_found(mock_db_session: MockSession, test_user: Users):
    app.dependency_overrides[get_db] = lambda: mock_db_session
    app.dependency_overrides[get_current_user] = lambda: {"id": test_user.id, "username": test_user.username, "role": test_user.role}

    response = client.delete("/todos/999")  # Non-existent ID
    assert response.status_code == 404
    assert response.json() == {"detail": "Todo not found"}

# Reset dependency overrides after tests (optional, good practice)
@pytest.fixture(autouse=True, scope="module")
def reset_dependencies():
    yield
    app.dependency_overrides = {}
