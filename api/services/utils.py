from functools import wraps
from flask import current_app as app
from ..db import db
from sqlalchemy.exc import SQLAlchemyError

def transactional(f):
    """
    Decorator to handle database transactions safely.
    Will commit the transaction if successful, rollback if there's an error.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            result = f(*args, **kwargs)
            db.session.commit()
            return result
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Transaction failed: {str(e)}", exc_info=True)
            raise SQLAlchemyError(f"Database transaction failed: {str(e)}")
    return decorated_function 