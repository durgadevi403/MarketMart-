import os
from flask import Flask, render_template
from config import config_by_name
from app.database import init_db, close_db, get_db

def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.config.from_object(config_by_name.get(config_name, config_by_name['default']))

    # Initialize database teardown
    app.teardown_appcontext(close_db)

    # Register custom template filters
    @app.template_filter('currency')
    def currency_filter(value):
        try:
            val = float(value)
            return f"${val:,.2f}"
        except (ValueError, TypeError):
            return "$0.00"

    @app.template_filter('datetime_format')
    def datetime_format_filter(value, fmt='%b %d, %Y %I:%M %p'):
        if not value:
            return '-'
        try:
            from datetime import datetime
            if isinstance(value, str):
                # Clean up sqlite format if needed
                val = value.replace('T', ' ')
                dt = datetime.fromisoformat(val)
            else:
                dt = value
            return dt.strftime(fmt)
        except Exception:
            return str(value)

    @app.template_filter('date_format')
    def date_format_filter(value, fmt='%b %d, %Y'):
        if not value:
            return '-'
        try:
            from datetime import datetime, date
            if isinstance(value, str):
                dt = datetime.strptime(value[:10], '%Y-%m-%d').date()
            elif isinstance(value, datetime):
                dt = value.date()
            elif isinstance(value, date):
                dt = value
            else:
                return str(value)
            return dt.strftime(fmt)
        except Exception:
            return str(value)

    # Global context processor
    @app.context_processor
    def inject_global_data():
        return {
            'store_name': app.config.get('STORE_NAME', 'MarketMate'),
            'store_address': app.config.get('STORE_ADDRESS', ''),
            'store_phone': app.config.get('STORE_PHONE', ''),
            'currency_symbol': app.config.get('CURRENCY_SYMBOL', '$'),
            'default_tax_rate': app.config.get('DEFAULT_TAX_RATE', 5.0)
        }

    # Register Blueprints
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.products import products_bp
    from app.routes.suppliers import suppliers_bp
    from app.routes.inventory import inventory_bp
    from app.routes.pos import pos_bp
    from app.routes.reports import reports_bp
    from app.routes.users import users_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dashboard_bp, url_prefix='')
    app.register_blueprint(products_bp, url_prefix='/products')
    app.register_blueprint(suppliers_bp, url_prefix='/suppliers')
    app.register_blueprint(inventory_bp, url_prefix='/inventory')
    app.register_blueprint(pos_bp, url_prefix='/pos')
    app.register_blueprint(reports_bp, url_prefix='/reports')
    app.register_blueprint(users_bp, url_prefix='/users')

    # Register error handlers
    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template('errors/500.html'), 500

    # CLI commands
    @app.cli.command('init-db')
    def init_db_command():
        """Initialize database tables."""
        init_db(app.config['DATABASE_PATH'])
        print(f"Database initialized at {app.config['DATABASE_PATH']}.")

    @app.cli.command('seed-db')
    def seed_db_command():
        """Seed database with realistic initial data."""
        from seed_data import seed_database
        init_db(app.config['DATABASE_PATH'])
        seed_database(app.config['DATABASE_PATH'])
        print("Database successfully seeded.")

    return app
