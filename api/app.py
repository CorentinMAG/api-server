from flask import Flask
from .config import Config
from .services import ServiceContainer
from api.models import db
import logging
from sqlalchemy_utils import create_database, database_exists
from dtr_common.logs.logger import create_logger

class DTRFlask(Flask):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._settings: Config | None = None
        self._services = None
        self._repositories = None
        self._logger: logging.Logger | None = None

    @property
    def settings(self) -> Config | None:
        return self._settings
    
    @settings.setter
    def settings(self, value: Config) -> None:
        self._settings = value

    @property
    def services(self) -> ServiceContainer:
        """lazy load service container"""
        if self._services is None:
            self._services = ServiceContainer()
        return self._services
    
    @property
    def logger(self) -> logging.Logger:
        if self._logger is None:
            raise ValueError("you must call init_logger before")
        return self._logger
    
    def init_logger(self) -> None:
        if self._settings is not None:
            self._logger = create_logger(
                "API",
                self._settings.LOG_LEVEL,
                self._settings.API_VERSION,
                self._settings.SYSTEM_NAME,
                self._settings.SYSTEM_VERSION,
                "raw" if self._settings.DEBUG else "json"
            )
    
    def init_database(self) -> None:
        if self.settings is None:
            raise NotImplementedError("you must set settings before initialize database")
        if not self.settings.DATABASE_URL:
            raise ValueError("DATABASE_URL is not set, make to define the DTR_DB_PASSWORD variable")

        config = {
            "SQLALCHEMY_DATABASE_URI": self.settings.DATABASE_URL,
            "SQLALCHEMY_ENGINE_OPTIONS": self.settings.SQLALCHEMY_ENGINE_OPTIONS
        }
        self.config.update(config)
        db.init_app(self)
        if self.settings.CREATE_DB:
            with self.app_context():
                if not database_exists(db.engine.url):
                    create_database(db.engine.url)
                    self.logger.info("New database %s created", self.settings.DB_NAME)
                else:
                    db.create_all()
                    self.logger.debug("Database tables have been created")