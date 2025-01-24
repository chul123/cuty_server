from flask import Blueprint, request, jsonify
from src.services.school_service import SchoolService

school_bp = Blueprint('school', __name__)

@school_bp.route('/', methods=['GET'])
def get_countries():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search = request.args.get('search', '')
    
    try:
        result = SchoolService.get_countries(page, per_page, search)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@school_bp.route('/<int:country_id>/schools', methods=['GET'])
def get_schools_by_country(country_id):
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search = request.args.get('search', '')
    
    try:
        result = SchoolService.get_schools_by_country(country_id, page, per_page, search)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@school_bp.route('/<int:country_id>/schools/<int:school_id>/colleges', methods=['GET'])
def get_colleges(country_id, school_id):
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search = request.args.get('search', '')
    
    try:
        result = SchoolService.get_colleges(country_id, school_id, page, per_page, search)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@school_bp.route('/<int:country_id>/schools/<int:school_id>/colleges/<int:college_id>/departments', methods=['GET'])
def get_departments(country_id, school_id, college_id):
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search = request.args.get('search', '')
    
    try:
        result = SchoolService.get_departments(country_id, school_id, college_id, page, per_page, search)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500
