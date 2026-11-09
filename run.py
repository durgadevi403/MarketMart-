import os
from app import create_app
from app.database import init_db

app = create_app(os.environ.get('FLASK_ENV', 'development'))

if __name__ == '__main__':
    # Ensure database exists
    init_db(app.config['DATABASE_PATH'])
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=app.config.get('DEBUG', True))
