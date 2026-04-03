"""
Characterization Tests for Configuration System

These tests capture the current behavior of the Config system
to ensure behavior preservation during Phase 2 API layer integration.
"""

import pytest
from pathlib import Path
import yaml
from src.core.config import Config


class TestConfigCharacterization:
    """
    Characterization tests for Config behavior

    These tests document existing behavior to prevent regressions
    when integrating with the API layer.
    """

    @pytest.fixture
    def sample_config_file(self, tmp_path):
        """Create sample configuration file"""
        config_path = tmp_path / "config.yaml"
        config_content = {
            "database": {
                "host": "localhost",
                "port": 5432,
                "name": "test_db",
            },
            "redis": {"host": "localhost", "port": 6379, "db": 0},
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            },
            "plugins": {"auto_load": True, "enabled": ["csv", "postgresql"]},
        }

        with open(config_path, "w") as f:
            yaml.dump(config_content, f)

        return str(config_path)

    @pytest.fixture
    def config(self, sample_config_file):
        """Create config instance for testing"""
        config = Config(sample_config_file, env_prefix="APP")
        config.load()
        return config

    def test_config_initialization(self, sample_config_file):
        """Characterize: Config initialization parameters"""
        config = Config(sample_config_file, env_prefix="APP")

        assert config._config_path == Path(sample_config_file)
        assert config._env_prefix == "APP_"

    def test_load_yaml_file(self, sample_config_file):
        """Characterize: YAML file loading behavior"""
        config = Config(sample_config_file)
        config.load()

        assert config.database.host == "localhost"
        assert config.database.port == 5432
        assert config.redis.host == "localhost"

    def test_get_dot_notation(self, config):
        """Characterize: Dot notation access to config values"""
        assert config.get("database.host") == "localhost"
        assert config.get("database.port") == 5432
        assert config.get("redis.port") == 6379

    def test_get_with_default(self, config):
        """Characterize: Default value for missing keys"""
        assert config.get("nonexistent.key", "default") == "default"
        assert config.get("database.nonexistent", 42) == 42

    def test_dictionary_style_access(self, config):
        """Characterize: Dictionary-style access to config"""
        db_config = config["database"]
        assert db_config["host"] == "localhost"
        assert db_config["port"] == 5432

    def test_attribute_style_access(self, config):
        """Characterize: Attribute-style access to config"""
        assert config.database.host == "localhost"
        assert config.database.port == 5432
        assert config.redis.host == "localhost"

    def test_to_dict_export(self, config):
        """Characterize: Dictionary export behavior"""
        config_dict = config.to_dict()

        assert isinstance(config_dict, dict)
        assert "database" in config_dict
        assert "redis" in config_dict
        assert config_dict["database"]["host"] == "localhost"

    def test_export_to_yaml(self, config, tmp_path):
        """Characterize: YAML export behavior"""
        export_path = tmp_path / "exported.yaml"

        yaml_str = config.export_to_yaml(path=str(export_path))

        assert export_path.exists()
        assert "database:" in yaml_str
        assert "redis:" in yaml_str

    def test_environment_variable_override(self, sample_config_file, monkeypatch):
        """Characterize: Environment variable override behavior"""
        monkeypatch.setenv("APP_DATABASE_HOST", "customhost")
        monkeypatch.setenv("APP_REDIS_HOST", "customhost")

        config = Config(sample_config_file, env_prefix="APP")
        config.load()

        assert config.database.host == "customhost"
        assert config.redis.host == "customhost"

    def test_merge_multiple_config_files(self, tmp_path):
        """Characterize: Multiple config file merging"""
        base_config = tmp_path / "base.yaml"
        override_config = tmp_path / "override.yaml"

        base_content = {
            "database": {"path": ":memory:", "max_connections": 10},
            "redis": {"host": "localhost"},
        }
        override_content = {
            "database": {"max_connections": 20},
            "logging": {"level": "DEBUG"},
        }

        base_config.write_text(yaml.dump(base_content))
        override_config.write_text(yaml.dump(override_content))

        config = Config([base_config, override_config])
        config.load()

        # Base values preserved
        assert config.database.path == ":memory:"
        assert config.redis.host == "localhost"

        # Override values applied
        assert config.database.max_connections == 20
        assert config.logging.level == "DEBUG"

    def test_reload_configuration(self, config, sample_config_file):
        """Characterize: Configuration reload behavior"""
        initial_host = config.database.host

        # Modify config file
        with open(sample_config_file, "r") as f:
            content = yaml.safe_load(f)
        content["database"]["host"] = "modifiedhost"

        with open(sample_config_file, "w") as f:
            yaml.dump(content, f)

        config.reload()

        assert config.database.host == "modifiedhost"

    def test_observer_notification(self, config):
        """Characterize: Observer notification on reload"""
        notifications = []

        def observer_callback():
            notifications.append("reloaded")

        config.add_observer(observer_callback)

        config.reload()

        assert len(notifications) == 1
        assert notifications[0] == "reloaded"

    def test_thread_safe_concurrent_access(self, sample_config_file):
        """Characterize: Thread-safe concurrent config access"""
        import threading

        config = Config(sample_config_file)
        config.load()

        results = []
        errors = []

        def read_config(thread_id):
            try:
                value = config.get("database.port")
                results.append((thread_id, value))
            except Exception as e:
                errors.append((thread_id, e))

        threads = [threading.Thread(target=read_config, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert len(results) == 10
        for thread_id, value in results:
            assert value == 5432

    def test_hot_reload_feature(self, sample_config_file):
        """Characterize: Hot-reload feature (if watchdog available)"""
        config = Config(sample_config_file, hot_reload=True)
        config.load()

        # Hot-reload capability check
        # Note: Actual hot-reload behavior depends on watchdog availability
        assert config.hot_reload_enabled is True

    def test_config_validation_error(self, tmp_path):
        """Characterize: Validation error handling"""
        invalid_config = tmp_path / "invalid.yaml"
        invalid_config.write_text("invalid: yaml: content: [")

        config = Config(str(invalid_config))

        with pytest.raises(yaml.YAMLError):
            config.load()

    def test_empty_config_file(self, tmp_path):
        """Characterize: Empty config file handling"""
        empty_config = tmp_path / "empty.yaml"
        empty_config.write_text("")

        config = Config(str(empty_config))

        with pytest.raises(ValueError, match="Empty configuration file"):
            config.load()

    def test_nonexistent_config_file(self, tmp_path):
        """Characterize: Nonexistent config file handling"""
        config = Config(str(tmp_path / "nonexistent.yaml"))

        with pytest.raises(FileNotFoundError):
            config.load()
