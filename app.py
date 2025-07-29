from bson.objectid import ObjectId
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from pymongo import MongoClient
import os
from datetime import datetime
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY')

# MongoDB Atlas configuration
MONGO_URI = os.environ.get('MONGO_URI')
client = MongoClient(MONGO_URI)
DB_NAME = os.environ.get('DB_NAME', 'fest_sponsor_db')
db = client[DB_NAME]

# Collections
sponsors_collection = db.sponsors
alumni_collection = db.alumni
speakers_collection = db.speakers
users_collection = db.users

# Default admin user (credentials from environment variables)
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME')
ADMIN_PASSWORD_RAW = os.environ.get('ADMIN_PASSWORD')
DEFAULT_ADMIN = {
    'username': ADMIN_USERNAME,
    'password': generate_password_hash(ADMIN_PASSWORD_RAW),
    'role': 'admin'
}

# Default moderator user (credentials from environment variables)
MODERATOR_USERNAME = os.environ.get('NORMAL_USERNAME')
MODERATOR_PASSWORD_RAW = os.environ.get('NORMAL_PASSWORD')
DEFAULT_MODERATOR = {
    'username': MODERATOR_USERNAME,
    'password': generate_password_hash(MODERATOR_PASSWORD_RAW),
    'role': 'moderator'
}

def init_admin():
    """Initialize default admin user if not exists"""
    # Add admin if not exists
    if DEFAULT_ADMIN['username'] and not users_collection.find_one({'username': DEFAULT_ADMIN['username']}):
        users_collection.insert_one(DEFAULT_ADMIN)
    # Add moderator if not exists
    if DEFAULT_MODERATOR['username'] and not users_collection.find_one({'username': DEFAULT_MODERATOR['username']}):
        users_collection.insert_one(DEFAULT_MODERATOR)

@app.before_request
def before_request():
    init_admin()

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = users_collection.find_one({'username': username})
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = str(user['_id'])
            session['username'] = user['username']
            session['role'] = user.get('role', 'user')
            flash(f"Login successfully!", 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password!', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('login'))

def login_required(f):
    """Decorator to require login for routes"""
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# API to get sponsor details by ID
@app.route('/api/sponsors/<sponsor_id>', methods=['GET'])
@login_required
def get_sponsor_details(sponsor_id):
    try:
        sponsor = sponsors_collection.find_one({'_id': ObjectId(sponsor_id)})
        if not sponsor:
            return jsonify({'error': 'Sponsor not found'}), 404
        sponsor['_id'] = str(sponsor['_id'])
        return jsonify(sponsor)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Sponsor management routes
@app.route('/sponsors')
@login_required
def sponsors():
    from os import environ
    admin_username = environ.get('ADMIN_USERNAME')
    is_admin = session.get('username') == admin_username
    moderator_only = not is_admin
    return render_template('sponsors.html', is_admin=is_admin, moderator_only=moderator_only)

# Alumni management routes
@app.route('/alumni')
@login_required
def alumni():
    from os import environ
    admin_username = environ.get('ADMIN_USERNAME')
    is_admin = session.get('username') == admin_username
    moderator_only = not is_admin
    return render_template('alumni.html', is_admin=is_admin, moderator_only=moderator_only)

# Speaker management routes
@app.route('/speakers')
@login_required
def speakers():
    from os import environ
    admin_username = environ.get('ADMIN_USERNAME')
    is_admin = session.get('username') == admin_username
    moderator_only = not is_admin
    return render_template('speakers.html', is_admin=is_admin, moderator_only=moderator_only)

@app.route('/api/sponsors/search', methods=['POST'])
@login_required
def search_sponsors():
    search_term = request.json.get('search_term', '')
    if search_term:
        regex = re.compile(re.escape(search_term), re.IGNORECASE)
        sponsors = list(sponsors_collection.find({
            '$or': [
                {'company_name': regex},
                {'website': regex},
                {'sponsor_mail': regex}
            ]
        }))
        # Only return required fields
        filtered = []
        for sponsor in sponsors:
            filtered.append({
                'company_name': sponsor.get('company_name', ''),
                'previous_sponsor': sponsor.get('previous_sponsor', ''),
                'website': sponsor.get('website', ''),
                'sponsor_mail': sponsor.get('sponsor_mail', '')
            })
        sponsors = filtered
    else:
        sponsors = []
    return jsonify(sponsors)

@app.route('/api/sponsors/add', methods=['POST'])
@login_required
def add_sponsor():
    if session.get('role') not in ['admin', 'moderator']:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    # Required fields
    company_name = request.json.get('company_name', '').strip()
    website = request.json.get('website', '').strip()
    sponsor_mail = request.json.get('sponsor_mail', '').strip()
    category = request.json.get('category', '').strip()
    # Basic validation for required fields
    if not company_name or not website or not sponsor_mail or not category:
        return jsonify({'success': False, 'message': 'Missing required fields'}), 400
    try:
        sponsor_data = {
            'company_name': company_name,
            'website': website,
            'sponsor_mail': sponsor_mail,
            'category': category,
            'created_at': datetime.utcnow(),
            'created_by': session.get('username')
        }
        result = sponsors_collection.insert_one(sponsor_data)
        return jsonify({'success': True, 'message': 'Sponsor added successfully', 'id': str(result.inserted_id)})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/sponsors/list')
@login_required
def list_sponsors():
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    try:
        sponsors = list(sponsors_collection.find().sort('created_at', -1))
        filtered = []
        for sponsor in sponsors:
            filtered.append({
                '_id': str(sponsor.get('_id', '')),
                'company_name': sponsor.get('company_name', ''),
                'website': sponsor.get('website', ''),
                'ruetian_name': sponsor.get('ruetian_name', ''),
                'category': sponsor.get('category', '')
            })
        return jsonify(filtered)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
from flask import send_file
import io
import pandas as pd
@app.route('/api/sponsors/download')
@login_required
def download_sponsors():
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    try:
        sponsors = list(sponsors_collection.find().sort('created_at', -1))
        data = []
        for sponsor in sponsors:
            data.append({
                'Company Name': sponsor.get('company_name', ''),
                'Website': sponsor.get('website', ''),
                'Ruetian Name': sponsor.get('ruetian_name', ''),
                'Category': sponsor.get('category', ''),
                'Sponsor Mail': sponsor.get('sponsor_mail', ''),
                'CTO Phone': sponsor.get('cto_phone', ''),
                'CEO Phone': sponsor.get('ceo_phone', ''),
                'CEO Mail': sponsor.get('ceo_mail', ''),
                'Previous Sponsor': sponsor.get('previous_sponsor', ''),
                'Ruetian Phone': sponsor.get('ruetian_phone', ''),
                'Ruetian Mail': sponsor.get('ruetian_mail', ''),
                'Ruetian LinkedIn': sponsor.get('ruetian_linkedin', ''),
                'Other Category': sponsor.get('other_category', ''),
                'Created At': sponsor.get('created_at', '').strftime('%Y-%m-%d %H:%M:%S') if sponsor.get('created_at') else ''
            })
        df = pd.DataFrame(data)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Sponsors')
        output.seek(0)
        return send_file(output, download_name='sponsors_list.xlsx', as_attachment=True, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sponsors/count')
@login_required
def count_sponsors():
    try:
        count = sponsors_collection.count_documents({})
        return jsonify({'count': count})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sponsors/delete/<sponsor_id>', methods=['DELETE'])
@login_required
def delete_sponsor(sponsor_id):
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    try:
        from bson.objectid import ObjectId
        result = sponsors_collection.delete_one({'_id': ObjectId(sponsor_id)})
        if result.deleted_count:
            return jsonify({'success': True, 'message': 'Sponsor deleted successfully'})
        else:
            return jsonify({'success': False, 'message': 'Sponsor not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
@app.route('/api/sponsors/update/<sponsor_id>', methods=['PUT'])
@login_required
def update_sponsor(sponsor_id):
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    try:
        from bson.objectid import ObjectId
        update_data = request.json
        # Website must be filled
        website = update_data.get('website', '').strip()
        if not website:
            return jsonify({'success': False, 'message': 'Website is required'}), 400
        # CTO Phone is optional, no validation needed
        result = sponsors_collection.update_one(
            {'_id': ObjectId(sponsor_id)},
            {'$set': update_data}
        )
        if result.matched_count:
            return jsonify({'success': True, 'message': 'Sponsor updated successfully'})
        else:
            return jsonify({'success': False, 'message': 'Sponsor not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# Generic API routes for other entities
# Only for alumni and speakers now

def create_entity_routes(entity_name, collection):
    @app.route(f'/api/{entity_name}/search', methods=['POST'], endpoint=f'search_{entity_name}')
    @login_required
    def search_entity():
        try:
            search_term = request.json.get('search_term', '')
            entities = []
            if search_term:
                regex = re.compile(re.escape(search_term), re.IGNORECASE)
                if entity_name == 'speakers':
                    entities = list(collection.find({
                        '$or': [
                            {'name': {'$regex': regex}},
                            {'mail': {'$regex': regex}},
                            {'linkedin': {'$regex': regex}},
                            {'designation': {'$regex': regex}}
                        ]
                    }))
                else:
                    entities = list(collection.find({
                        '$or': [
                            {'ruetian_name': {'$regex': regex}},
                            {'ruetian_mail': {'$regex': regex}},
                            {'ruetian_linkedin': {'$regex': regex}}
                        ]
                    }))
            else:
                entities = list(collection.find().sort('created_at', -1))
            for entity in entities:
                entity['_id'] = str(entity['_id'])
            return jsonify(entities)
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route(f'/api/{entity_name}/add', methods=['POST'], endpoint=f'add_{entity_name}')
    @login_required
    def add_entity():
        # Only allow admin or moderator to add
        from os import environ
        admin_username = environ.get('ADMIN_USERNAME')
        is_admin = session.get('username') == admin_username
        if entity_name == 'alumni' and not (is_admin or session.get('role') == 'moderator'):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        if entity_name == 'speakers' and not (is_admin or session.get('role') == 'moderator'):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        try:
            # Ensure JSON body
            if not request.is_json:
                return jsonify({'success': False, 'message': 'Request must be JSON'}), 400
            data = request.get_json()
            # Basic validation for required fields
            if entity_name == 'speakers':
                required_fields = ['name', 'linkedin', 'designation']
                for field in required_fields:
                    if not data.get(field):
                        return jsonify({'success': False, 'message': f'Missing required field: {field}'}), 400
            # Insert into collection
            result = collection.insert_one(data)
            return jsonify({'success': True, 'message': f'{entity_name.title()[:-1]} added successfully', 'id': str(result.inserted_id)})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    @app.route(f'/api/{entity_name}/list', endpoint=f'list_{entity_name}')
    @login_required
    def list_entities():
        from os import environ
        admin_username = environ.get('ADMIN_USERNAME')
        is_admin = session.get('username') == admin_username
        # Only admin can list for alumni and speakers
        if entity_name in ['alumni', 'speakers'] and not is_admin:
            return jsonify({'error': 'Unauthorized'}), 403
        try:
            entities = list(collection.find().sort('created_at', -1))
            for entity in entities:
                entity['_id'] = str(entity['_id'])
            return jsonify(entities)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    @app.route(f'/api/{entity_name}/download', endpoint=f'download_{entity_name}')
    @login_required
    def download_entities():
        from os import environ
        admin_username = environ.get('ADMIN_USERNAME')
        is_admin = session.get('username') == admin_username
        # Only admin can download for alumni and speakers
        if entity_name in ['alumni', 'speakers'] and not is_admin:
            return jsonify({'error': 'Unauthorized'}), 403
        try:
            entities = list(collection.find().sort('created_at', -1))
            data = []
            if entity_name == 'alumni':
                for a in entities:
                    data.append({
                        'Ruetian Name': a.get('ruetian_name', ''),
                        'Ruetian Phone': a.get('ruetian_phone', ''),
                        'Ruetian Mail': a.get('ruetian_mail', ''),
                        'Ruetian LinkedIn': a.get('ruetian_linkedin', ''),
                        'Created At': a.get('created_at', '').strftime('%Y-%m-%d %H:%M:%S') if a.get('created_at') else '',
                        'Created By': a.get('created_by', '')
                    })
                import io
                import pandas as pd
                from flask import send_file
                df = pd.DataFrame(data)
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False, sheet_name='Alumni')
                output.seek(0)
                return send_file(output, download_name='alumni_list.xlsx', as_attachment=True, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            if entity_name == 'speakers':
                for s in entities:
                    data.append({
                        'Name': s.get('name', ''),
                        'Phone': s.get('phone', ''),
                        'Mail': s.get('mail', ''),
                        'LinkedIn': s.get('linkedin', ''),
                        'Designation': s.get('designation', ''),
                        'Created At': s.get('created_at', '').strftime('%Y-%m-%d %H:%M:%S') if s.get('created_at') else '',
                        'Created By': s.get('created_by', '')
                    })
                import io
                import pandas as pd
                from flask import send_file
                df = pd.DataFrame(data)
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False, sheet_name='Speakers')
                output.seek(0)
                return send_file(output, download_name='speakers_list.xlsx', as_attachment=True, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route(f'/api/{entity_name}/count', endpoint=f'count_{entity_name}')
    @login_required
    def count_entities():
        try:
            count = collection.count_documents({})
            return jsonify({'count': count})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route(f'/api/{entity_name}/delete/<entity_id>', methods=['DELETE'], endpoint=f'delete_{entity_name}')
    @login_required
    def delete_entity(entity_id):
        from os import environ
        admin_username = environ.get('ADMIN_USERNAME')
        is_admin = session.get('username') == admin_username
        # Only admin can delete for alumni and speakers
        if entity_name in ['alumni', 'speakers'] and not is_admin:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        try:
            from bson.objectid import ObjectId
            result = collection.delete_one({'_id': ObjectId(entity_id)})
            if result.deleted_count:
                return jsonify({'success': True, 'message': f'{entity_name.title()[:-1]} deleted successfully'})
            else:
                return jsonify({'success': False, 'message': f'{entity_name.title()[:-1]} not found'}), 404
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500
    @app.route(f'/api/{entity_name}/update/<entity_id>', methods=['PUT'], endpoint=f'update_{entity_name}')
    @login_required
    def update_entity(entity_id):
        from os import environ
        admin_username = environ.get('ADMIN_USERNAME')
        is_admin = session.get('username') == admin_username
        # Only admin can update for alumni and speakers
        if entity_name in ['alumni', 'speakers'] and not is_admin:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        try:
            from bson.objectid import ObjectId
            update_data = request.json
            result = collection.update_one(
                {'_id': ObjectId(entity_id)},
                {'$set': update_data}
            )
            if result.matched_count:
                return jsonify({'success': True, 'message': f'{entity_name.title()[:-1]} updated successfully'})
            else:
                return jsonify({'success': False, 'message': f'{entity_name.title()[:-1]} not found'}), 404
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500
    # No need to set __name__ since endpoint is now unique

# Create routes for alumni and speakers only
create_entity_routes('alumni', alumni_collection)
create_entity_routes('speakers', speakers_collection)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
