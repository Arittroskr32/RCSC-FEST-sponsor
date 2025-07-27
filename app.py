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

def init_admin():
    """Initialize default admin user if not exists"""
    if not users_collection.find_one({'username': DEFAULT_ADMIN['username']}):
        users_collection.insert_one(DEFAULT_ADMIN)

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
            flash('Login successful!', 'success')
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

# Sponsor management routes
@app.route('/sponsors')
@login_required
def sponsors():
    return render_template('sponsors.html')

# Alumni management routes
@app.route('/alumni')
@login_required
def alumni():
    return render_template('alumni.html')

# Speaker management routes
@app.route('/speakers')
@login_required
def speakers():
    return render_template('speakers.html')

@app.route('/api/sponsors/search', methods=['POST'])
@login_required
def search_sponsors():
    search_term = request.json.get('search_term', '')
    if search_term:
        regex = re.compile(re.escape(search_term), re.IGNORECASE)
        sponsors = list(sponsors_collection.find({
            '$or': [
                {'company_name': regex},
                {'website': regex}
            ]
        }))
        # Only return required fields
        filtered = []
        for sponsor in sponsors:
            filtered.append({
                'company_name': sponsor.get('company_name', ''),
                'previous_sponsor': sponsor.get('previous_sponsor', ''),
                'website': sponsor.get('website', '')
            })
        sponsors = filtered
    else:
        sponsors = []
    return jsonify(sponsors)

@app.route('/api/sponsors/add', methods=['POST'])
@login_required
def add_sponsor():
    try:
        sponsor_data = {
            'company_name': request.json.get('company_name'),
            'cto_phone': request.json.get('cto_phone') or None,
            'ceo_phone': request.json.get('ceo_phone'),
            'ceo_mail': request.json.get('ceo_mail'),
            'previous_sponsor': request.json.get('previous_sponsor') if request.json.get('previous_sponsor') in ['yes', 'no', 'not idea'] else None,
            'website': request.json.get('website'),
            'sponsor_mail': request.json.get('sponsor_mail'),
            'ruetian_name': request.json.get('ruetian_name') or None,
            'ruetian_phone': request.json.get('ruetian_phone') or None,
            'ruetian_mail': request.json.get('ruetian_mail') or None,
            'ruetian_linkedin': request.json.get('ruetian_linkedin'),
            'category': request.json.get('category'),
            'other_category': request.json.get('other_category') if request.json.get('category') == 'others' else None,
            'created_at': datetime.now(),
            'created_by': session['username']
        }

        # Check if sponsor already exists (by company_name, cto_phone, or sponsor_mail)
        duplicate_query = {
            '$or': [
                {'company_name': sponsor_data['company_name']},
                {'cto_phone': sponsor_data['cto_phone']} if sponsor_data['cto_phone'] else {},
                {'sponsor_mail': sponsor_data['sponsor_mail']}
            ]
        }
        # Remove empty dicts from $or
        duplicate_query['$or'] = [q for q in duplicate_query['$or'] if q]
        existing = sponsors_collection.find_one(duplicate_query)
        if existing:
            return jsonify({'success': False, 'message': 'Company already exists.'}), 400

        result = sponsors_collection.insert_one(sponsor_data)
        return jsonify({'success': True, 'message': 'Sponsor added successfully', 'id': str(result.inserted_id)})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/sponsors/list')
@login_required
def list_sponsors():
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
    try:
        from bson.objectid import ObjectId
        update_data = request.json
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
        try:
            # Ensure JSON body
            if not request.is_json:
                return jsonify({'success': False, 'message': 'Request must be JSON'}), 400
            data = request.get_json()
            if entity_name == 'speakers':
                entity_data = {
                    'name': data.get('name'),
                    'phone': data.get('phone') or None,
                    'mail': data.get('mail') or None,
                    'linkedin': data.get('linkedin'),
                    'designation': data.get('designation'),
                    'created_at': datetime.now(),
                    'created_by': session['username']
                }
                existing = collection.find_one({
                    '$or': [
                        {'mail': entity_data.get('mail')},
                        {'name': entity_data.get('name')},
                        {'linkedin': entity_data.get('linkedin')}
                    ]
                })
            else:
                entity_data = {
                    'ruetian_name': data.get('ruetian_name'),
                    'ruetian_phone': data.get('ruetian_phone') or None,
                    'ruetian_mail': data.get('ruetian_mail'),
                    'ruetian_linkedin': data.get('ruetian_linkedin'),
                    'created_at': datetime.now(),
                    'created_by': session['username']
                }
                existing = collection.find_one({
                    '$or': [
                        {'ruetian_mail': entity_data.get('ruetian_mail')},
                        {'ruetian_name': entity_data.get('ruetian_name')},
                        {'ruetian_linkedin': entity_data.get('ruetian_linkedin')}
                    ]
                })
            if existing:
                if entity_name == 'speakers':
                    return jsonify({'success': False, 'message': "Speaker already exists (name, mail, or linkedin)"}), 400
                else:
                    return jsonify({'success': False, 'message': "Alumni already exists (name, mail, or linkedin)"}), 400
            result = collection.insert_one(entity_data)
            if entity_name == 'speakers':
                return jsonify({'success': True, 'message': "Speaker added successfully!", 'id': str(result.inserted_id)})
            else:
                return jsonify({'success': True, 'message': "Alumni added successfully!", 'id': str(result.inserted_id)})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    @app.route(f'/api/{entity_name}/list', endpoint=f'list_{entity_name}')
    @login_required
    def list_entities():
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
        try:
            entities = list(collection.find().sort('created_at', -1))
            data = []
            if entity_name == 'speakers':
                for entity in entities:
                    data.append({
                        'Name': entity.get('name', ''),
                        'Phone': entity.get('phone', ''),
                        'Mail': entity.get('mail', ''),
                        'LinkedIn': entity.get('linkedin', ''),
                        'Designation': entity.get('designation', ''),
                        'Created At': entity.get('created_at', '').strftime('%Y-%m-%d %H:%M:%S') if entity.get('created_at') else ''
                    })
            else:
                for entity in entities:
                    data.append({
                        'Ruetian Name': entity.get('ruetian_name', ''),
                        'Ruetian Phone': entity.get('ruetian_phone', ''),
                        'Ruetian Mail': entity.get('ruetian_mail', ''),
                        'Ruetian LinkedIn': entity.get('ruetian_linkedin', ''),
                        'Created At': entity.get('created_at', '').strftime('%Y-%m-%d %H:%M:%S') if entity.get('created_at') else ''
                    })
            from flask import send_file
            df = pd.DataFrame(data)
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name=entity_name.title())
            output.seek(0)
            return send_file(output, download_name=f'{entity_name}_list.xlsx', as_attachment=True, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
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
