import os

DEFAULT_NUMBER_OF_POSTS_IN_RESPONSE = int(os.getenv(
    "DEFAULT_NUMBER_OF_POSTS_IN_RESPONSE", 5
))
DEFAULT_NUMBER_OF_PARSED_POSTS = int(os.getenv("DEFAULT_NUMBER_OF_PARSED_POSTS", 30))
YAML_SCHEMA_PATH = os.getenv("YAML_SCHEMA_PATH", "webapp/api.yaml")
PSQL_DIR = os.getenv("PSQL_DIR", "psql")
REQUEST_THROTTLE_SECONDS = int(os.getenv("REQUEST_THROTTLE_SECONDS", 10))
HOST_TO_PARSE = os.getenv("HOST_TO_PARSE", "https://news.ycombinator.com/")
POSTGRES_CONNECT_URL = os.getenv(
    "POSTGRES_CONNECT_URL", "postgresql://postgres:pass@localhost:5432/postgres"
)
TEST_POSTGRES_CONNECT_URL = os.getenv(
    "TEST_POSTGRES_CONNECT_URL",
    "postgresql://posgres:pass@localhost:5432/test_postgres",
)
LOGGING_LEVEL = int(os.getenv("LOGGING_LEVEL", 10))
