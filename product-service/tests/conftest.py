"""
Pytest configuration and fixtures for Product Service tests.
"""
import pytest
from django.core.management import call_command
from django.db import connection


@pytest.fixture(scope='session')
def django_db_setup(django_db_setup, django_db_blocker):
    """
    Setup Django database for tests.
    This creates the database tables needed for Django User model.
    """
    with django_db_blocker.unblock():
        # Create database tables
        call_command('migrate', verbosity=0, interactive=False)


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """
    Enable database access for all tests.
    This is needed because we're using Django User model for JWT tokens.
    """
    pass
