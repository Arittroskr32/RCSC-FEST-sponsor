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

# Always validate session against .env for admin/moderator
@app.before_request
def validate_env_session():
    admin_username = os.environ.get('ADMIN_USERNAME')
    moderator_username = os.environ.get('MODERATOR_USERNAME')
    # Only check if logged in as admin/moderator
    if 'role' in session:
        if session['role'] == 'admin' and session.get('username') != admin_username:
            session.clear()
            flash('Admin credentials changed. Please log in again.', 'error')
            return redirect(url_for('login'))
        if session['role'] == 'moderator' and session.get('username') != moderator_username:
            session.clear()
            flash('Moderator credentials changed. Please log in again.', 'error')
            return redirect(url_for('login'))

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

        # Always check .env for admin/moderator
        admin_username = os.environ.get('ADMIN_USERNAME')
        admin_password = os.environ.get('ADMIN_PASSWORD')
        moderator_username = os.environ.get('MODERATOR_USERNAME')
        moderator_password = os.environ.get('NORMAL_PASSWORD')

        if username == admin_username and password == admin_password:
            session['user_id'] = 'admin'
            session['username'] = admin_username
            session['role'] = 'admin'
            flash("Login successfully!", 'success')
            return redirect(url_for('index'))
        elif username == moderator_username and password == moderator_password:
            session['user_id'] = 'moderator'
            session['username'] = moderator_username
            session['role'] = 'moderator'
            flash("Login successfully!", 'success')
            return redirect(url_for('index'))
        else:
            # Fallback to DB for other users
            user = users_collection.find_one({'username': username})
            if user and check_password_hash(user['password'], password):
                session['user_id'] = str(user['_id'])
                session['username'] = user['username']
                session['role'] = user.get('role', 'user')
                flash("Login successfully!", 'success')
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
    if session.get('role') not in ['admin', 'moderator']:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    # Required fields
    company_name = request.json.get('company_name', '').strip()
    website = request.json.get('website', '').strip()
    category = request.json.get('category', '').strip()
    # Basic validation for required fields
    if not company_name or not website or not category:
        return jsonify({'success': False, 'message': 'Missing required fields'}), 400
    try:
        sponsor_data = {
            'company_name': company_name,
            'previous_sponsor': request.json.get('previous_sponsor', ''),
            'website': website,
            'contacts': request.json.get('contacts', []),
            'ruetians': request.json.get('ruetians', []),
            'category': category,
            'other_category': request.json.get('other_category', ''),
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
            # Initialize contact fields
            contact_data = {
                'CEO Name': '',
                'CEO Phone': '',
                'CEO Mail': '',
                'CEO LinkedIn': '',
                'CTO Name': '',
                'CTO Phone': '',
                'CTO Mail': '',
                'CTO LinkedIn': '',
                'Brand Manager Name': '',
                'Brand Manager Phone': '',
                'Brand Manager Mail': '',
                'Brand Manager LinkedIn': '',
                'Sponsor Manager Name': '',
                'Sponsor Manager Phone': '',
                'Sponsor Manager Mail': '',
                'Sponsor Manager LinkedIn': '',
                'HR Name': '',
                'HR Phone': '',
                'HR Mail': '',
                'HR LinkedIn': ''
            }
            
            # Fill contact data from contacts array
            if sponsor.get('contacts'):
                for contact in sponsor['contacts']:
                    role = contact.get('role', '')
                    name = contact.get('name', '')
                    phone = contact.get('phone', '')
                    mail = contact.get('mail', '')
                    linkedin = contact.get('linkedin', '')
                    
                    if role == 'CEO':
                        contact_data['CEO Name'] = name
                        contact_data['CEO Phone'] = phone
                        contact_data['CEO Mail'] = mail
                        contact_data['CEO LinkedIn'] = linkedin
                    elif role == 'CTO':
                        contact_data['CTO Name'] = name
                        contact_data['CTO Phone'] = phone
                        contact_data['CTO Mail'] = mail
                        contact_data['CTO LinkedIn'] = linkedin
                    elif role == 'Brand Manager':
                        contact_data['Brand Manager Name'] = name
                        contact_data['Brand Manager Phone'] = phone
                        contact_data['Brand Manager Mail'] = mail
                        contact_data['Brand Manager LinkedIn'] = linkedin
                    elif role == 'Sponsor Manager':
                        contact_data['Sponsor Manager Name'] = name
                        contact_data['Sponsor Manager Phone'] = phone
                        contact_data['Sponsor Manager Mail'] = mail
                        contact_data['Sponsor Manager LinkedIn'] = linkedin
                    elif role == 'HR':
                        contact_data['HR Name'] = name
                        contact_data['HR Phone'] = phone
                        contact_data['HR Mail'] = mail
                        contact_data['HR LinkedIn'] = linkedin
            
            # Initialize ruetian fields (up to 5 ruetians)
            ruetian_data = {}
            for i in range(1, 6):  # Support up to 5 ruetians
                ruetian_data[f'Ruetian {i} Name'] = ''
                ruetian_data[f'Ruetian {i} Phone'] = ''
                ruetian_data[f'Ruetian {i} Mail'] = ''
                ruetian_data[f'Ruetian {i} LinkedIn'] = ''
            
            # Fill ruetian data from ruetians array
            if sponsor.get('ruetians'):
                for idx, ruetian in enumerate(sponsor['ruetians'][:5]):  # Limit to 5 ruetians
                    num = idx + 1
                    ruetian_data[f'Ruetian {num} Name'] = ruetian.get('name', '')
                    ruetian_data[f'Ruetian {num} Phone'] = ruetian.get('phone', '')
                    ruetian_data[f'Ruetian {num} Mail'] = ruetian.get('mail', '')
                    ruetian_data[f'Ruetian {num} LinkedIn'] = ruetian.get('linkedin', '')
            
            # Combine all data
            row_data = {
                'Company Name': sponsor.get('company_name', ''),
                'Website': sponsor.get('website', ''),
                'Previous Sponsor': sponsor.get('previous_sponsor', ''),
                'Category': sponsor.get('category', ''),
                'Other Category': sponsor.get('other_category', ''),
            }
            
            # Add contact data
            row_data.update(contact_data)
            
            # Add ruetian data
            row_data.update(ruetian_data)
            
            # Add metadata
            row_data.update({
                'Created At': sponsor.get('created_at', '').strftime('%Y-%m-%d %H:%M:%S') if sponsor.get('created_at') else '',
                'Created By': sponsor.get('created_by', '')
            })
            
            data.append(row_data)
        
        df = pd.DataFrame(data)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Sponsors')
            
            # Auto-adjust column widths
            worksheet = writer.sheets['Sponsors']
            for i, col in enumerate(df.columns):
                max_length = max(df[col].astype(str).map(len).max(), len(col))
                worksheet.set_column(i, i, min(max_length + 2, 50))  # Max width of 50
        
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
