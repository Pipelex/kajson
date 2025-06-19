import pytest

import kajson.kajson_manager


@pytest.fixture(scope="module", autouse=True)
def reset_kajson_manager_fixture():
    # Code to run before each test
    print("\n[magenta]Kajson setup[/magenta]")
    try:
        kajson_manager_instance = kajson.kajson_manager.KajsonManager()
    except Exception as exc:
        pytest.exit(f"Critical Kajson setup error: {exc}")
    yield
    # Code to run after each test
    print("\n[magenta]Kajson teardown[/magenta]")
    kajson_manager_instance.teardown()
