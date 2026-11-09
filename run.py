import os

from app import create_app
from app.database import init_db

# Load the Flask application using the production configuration
app = create_app(os.environ.get('FLASK_ENV', 'production'))


# Initialize the database whenever the application starts.
# This is important because Gunicorn does not execute
# the __main__ block below.
init_db(app.config['DATABASE_PATH'])


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))

    app.run(
        host='0.0.0.0',
        port=port,
        debug=app.config.get('DEBUG', False)
    )