"""
Controller for Renogy-related endpoints
"""
from quart import Blueprint, jsonify
from services.renogy_service import fetch_data

# Create Blueprint for Renogy routes
renogy_bp = Blueprint('renogy', __name__)

@renogy_bp.route('/renogy_data', methods=['GET'])
async def get_renogy_data():
    """Get data from Renogy devices"""
    return await fetch_data()