"""
Main application entry point
"""
import logging
from quart import Quart
from controllers.renogy_controller import renogy_bp
from controllers.system_controller import system_bp
from utils.middleware import add_cors_headers
from services.renogy_service import connect as connect_renogy
from config.settings import DEBUG, HOST, PORT

# Configure logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger('quart.app')
log.setLevel(logging.INFO)

# Create Quart app
app = Quart(__name__)

# Register blueprints
app.register_blueprint(renogy_bp)
app.register_blueprint(system_bp)

# Add CORS middleware
app.after_request(add_cors_headers)

# Connect to Renogy devices on startup
@app.before_serving
async def before_serving():
    await connect_renogy()

if __name__ == '__main__':
    app.run(debug=DEBUG, host=HOST, port=PORT)