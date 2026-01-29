from flask import Flask, g
from api.config import Config
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import sessionmaker, Session, scoped_session

class DTRApp(Flask):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._settings: Config | None = None
        self._engine: Engine | None = None
        self._session_factory: scoped_session | None = None

    @property
    def settings(self) -> Config:
        if self._settings is None:
            raise RuntimeError("settings not initialized")
        return self._settings
    
    @settings.setter
    def settings(self, value: Config) -> None:
        self._settings = value

    @property
    def engine(self) -> Engine:
        if self._engine is None:
            raise RuntimeError("Database engine not initialized")
        return self._engine
    
    @property
    def session(self) -> Session:
        """get current database session for this request context"""
        if "db_session" not in g:
            if self._session_factory is None:
                raise RuntimeError("Database session factory is not initialized")
            g.db_session = self._session_factory()
        return g.db_session
    
    def initialize(self) -> None:
        """initialize the application components"""
        self._initialize_error_handlers()
        self._initialize_database()
        self._initialize_appcontext()

    def _setup_session(self) -> None:
        """Ensure session is set up for each request"""
        if "db_session" not in g:
            g.db_session = self._session_factory()
    
    def _close_session(self, exception=None) -> None:
        """close session at the end of each request"""
        session = g.pop("db_session", None)
        if session is not None:
            session.close()

    def _initialize_error_handlers(self) -> None:
        from api.handlers import register_error_handlers
        register_error_handlers(self)

    def _initialize_database(self) -> None:
        self._engine = create_engine(
            self.settings.DATABASE_URL, 
            **self.settings.SQLALCHEMY_ENGINE_OPTIONS
        )
        self._session_factory = sessionmaker(autocommit=False, autoflush=False, bind=self._engine)

    def _initialize_appcontext(self) -> None:
        self.teardown_appcontext(self._close_session)
        self.before_request(self._setup_session)