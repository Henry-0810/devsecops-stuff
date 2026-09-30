import pytest
from pydantic import ValidationError


def test_title_is_trimmed(app_module):
    assert app_module.IdeaCreate(title="  Ship it  ").title == "Ship it"


@pytest.mark.parametrize("title", ["", "   ", "x" * 121])
def test_invalid_titles_are_rejected(app_module, title):
    with pytest.raises(ValidationError):
        app_module.IdeaCreate(title=title)


def test_description_limit(app_module):
    with pytest.raises(ValidationError):
        app_module.IdeaCreate(title="Idea", description="x" * 1001)


def test_partial_update_preserves_omitted_fields(app_module):
    update = app_module.IdeaUpdate(description=None)
    assert update.model_dump(exclude_unset=True) == {"description": None}


def test_update_rejects_explicit_null_title(app_module):
    with pytest.raises(ValidationError):
        app_module.IdeaUpdate(title=None)
