# -*- coding: utf-8 -*-
"""
Household Registration Module for CDC Voucher System

@author: Student Group
"""
from flask import Blueprint, request, jsonify, render_template
import json
import os
import random
from datetime import datetime

# Create Blueprint for household routes
household_bp = Blueprint('household', __name__)

"""
Declare and instantiate data structure.
"""

# JSON file path for storing household data
HOUSEHOLD_DATA_FILE = 'household_data.json'

# Dictionary to store registered users
users = {}

# Dictionary to store user sessions
active_sessions = {}

# Load existing household data from JSON file
def load_household_data():
    """Load household data from JSON file."""
    global users
    if os.path.exists(HOUSEHOLD_DATA_FILE):
        try:
            with open(HOUSEHOLD_DATA_FILE, 'r') as f:
                users = json.load(f)
            print(f'Loaded {len(users)} users from {HOUSEHOLD_DATA_FILE}')
        except Exception as e:
            print(f'Error loading data: {e}')
            users = {}
    else:
        users = {}

# Save household data to JSON file
def save_household_data():
    """Save household data to JSON file."""
    try:
        with open(HOUSEHOLD_DATA_FILE, 'w') as f:
            json.dump(users, f, indent=4)
        print(f'Saved {len(users)} users to {HOUSEHOLD_DATA_FILE}')
    except Exception as e:
        print(f'Error saving data: {e}')

# Generate unique household ID
def generate_household_id():
    """Generate a unique household ID with format 'H' + 11 digits."""
    while True:
        # Generate 11 random digits
        digits = ''.join([str(random.randint(0, 9)) for _ in range(11)])
        household_id = 'H' + digits

        # Check if this ID already exists
        existing_ids = [user_data.get('household_id') for user_data in users.values()]
        if household_id not in existing_ids:
            return household_id

# Initialize data on module load
load_household_data()

"""
Routes for household registration and management
"""

@household_bp.route('/', methods=['GET', 'POST'])
@household_bp.route('/register', methods=['GET', 'POST'])
def registerPage():
    """Household registration page"""
    # When users visit the registration page using GET method...
    if request.method == 'GET':
        return render_template('household_register.html')

    # When users submit registration information...
    if request.method == 'POST':
        input_email = request.form.get('email')
        input_name = request.form.get('name')
        input_nric = request.form.get('nric')

        # Check if email already exists (one household per email)
        existing_emails = [user_data.get('email') for user_data in users.values()]
        if input_email in existing_emails:
            # Console echo
            print(f'''
                  Function: Register New Household
                  Email: {input_email}
                  Status: Failure
                  Response: Email already registered.
                  ''')

            return render_template('household_error.html',
                                 title='Registration Failed',
                                 message='Email already registered. Each household can only register once.',
                                 details=f'Email: {input_email}',
                                 back_url='/household/register')

        # Check if NRIC already exists in the system
        all_nrics = [user_data.get('nric') for user_data in users.values()]
        if input_nric.upper() in all_nrics:
            # Console echo
            print(f'''
                  Function: Register New Household
                  NRIC: {input_nric}
                  Status: Failure
                  Response: NRIC already registered.
                  ''')

            return render_template('household_error.html',
                                 title='Registration Failed',
                                 message='This NRIC/FIN number is already registered.',
                                 details=f'NRIC: {input_nric}',
                                 back_url='/household/register')

        # If registration is success
        # Generate unique household ID
        household_id = generate_household_id()

        # Get current date and time
        date_created = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        users[household_id] = {
            'household_id': household_id,
            'name': input_name,
            'nric': input_nric.upper(),
            'email': input_email,
            'date_created': date_created,
            'status': 'Active'
        }

        # Save to JSON file
        save_household_data()

        # Console echo
        print(f'''
              Function: Register New Household
              Household ID: {household_id}
              Name: {input_name}
              NRIC/FIN: {input_nric}
              Email: {input_email}
              Date Created: {date_created}
              Status: Active
              Response: Household registered successfully.
              ''')

        return render_template('household_success.html',
                             household_id=household_id,
                             name=input_name,
                             nric=input_nric.upper(),
                             email=input_email,
                             date_created=date_created,
                             status='Active')


@household_bp.route('/view', methods=['GET', 'POST'])
def viewHousehold():
    """View household information"""
    # When users visit the view page using GET method...
    if request.method == 'GET':
        return render_template('household_view.html')

    # When users submit household ID and NRIC...
    if request.method == 'POST':
        input_household_id = request.form.get('household_id')
        input_nric = request.form.get('nric')

        # Check if household exists
        if input_household_id in users.keys():
            household = users[input_household_id]

            # Verify NRIC matches
            stored_nric = household.get('nric', '')
            if stored_nric != input_nric.upper():
                # Console echo
                print(f'''
                      Function: View Household
                      Household ID: {input_household_id}
                      Status: Failure
                      Response: NRIC mismatch.
                      ''')

                return render_template('household_error.html',
                                     title='Verification Failed',
                                     message='NRIC does not match the household record.',
                                     details=None,
                                     back_url='/household/view')

            # NRIC matches, proceed to show information
            # Console echo
            print(f'''
                  Function: View Household
                  Household ID: {input_household_id}
                  Status: Success
                  Response: Household found and verified.
                  ''')

            return render_template('household_info.html',
                                 household_id=input_household_id,
                                 name=household.get('name', 'N/A'),
                                 nric=household.get('nric', 'N/A'),
                                 email=household['email'],
                                 date_created=household.get('date_created', 'N/A'),
                                 status=household.get('status', 'Active'))
        else:
            # Console echo
            print(f'''
                  Function: View Household
                  Household ID: {input_household_id}
                  Status: Failure
                  Response: Household not found.
                  ''')

            return render_template('household_error.html',
                                 title='Household Not Found',
                                 message='Household ID not found. Please register first.',
                                 details=f'Household ID: {input_household_id}',
                                 back_url='/household/view')


"""
API endpoints
"""

@household_bp.route('/api/all', methods=['GET'])
def getHouseholdAPI():
    """Return all household data in JSON format."""
    # Reload data to ensure we have the latest voucher balances
    load_household_data()
    return jsonify({
        'status': 'success',
        'total_households': len(users),
        'households': users
    })


@household_bp.route('/api/<household_id>', methods=['GET'])
def getHouseholdByIdAPI(household_id):
    """Get specific household info"""
    # Reload data to ensure we have the latest voucher balances
    load_household_data()

    if household_id in users.keys():
        household = users[household_id]
        # Return all household data including voucher balances
        return jsonify({
            'status': 'success',
            'household_id': household_id,
            **household  # Spread all household fields
        })
    else:
        return jsonify({
            'status': 'error',
            'message': f'Household "{household_id}" not found.'
        })


@household_bp.route('/api/nric/<nric>', methods=['GET'])
def checkNRICAPI(nric):
    """Check if an NRIC is registered and can claim vouchers."""
    nric = nric.upper()

    # Search through all households for this NRIC
    for household_id, household in users.items():
        if household.get('nric') == nric:
            return jsonify({
                'status': 'success',
                'nric': nric,
                'registered': True,
                'household_id': household_id,
                'name': household.get('name')
            })

    return jsonify({
        'status': 'success',
        'nric': nric,
        'registered': False,
        'message': 'NRIC not registered in any household.'
    })


@household_bp.route('/api/update/<household_id>', methods=['PUT', 'PATCH', 'POST'])
def updateHouseholdAPI(household_id):
    """Update household voucher balances (used for redemption)"""
    # Reload data to ensure we have the latest
    load_household_data()

    if household_id not in users:
        return jsonify({
            'status': 'error',
            'message': f'Household "{household_id}" not found.'
        }), 404

    # Get update data from request
    data = request.get_json(silent=True) or {}

    # Update voucher balances if provided
    if '2' in data:
        users[household_id]['2'] = int(data['2'])
    if '5' in data:
        users[household_id]['5'] = int(data['5'])
    if '10' in data:
        users[household_id]['10'] = int(data['10'])

    # Save to file
    save_household_data()

    return jsonify({
        'status': 'success',
        'message': 'Household updated successfully',
        'household_id': household_id,
        'updated_balances': {
            '2': users[household_id].get('2', 0),
            '5': users[household_id].get('5', 0),
            '10': users[household_id].get('10', 0)
        }
    }), 200


@household_bp.route('/api/claim', methods=['POST'])
def claimVoucherAPI():
    """API endpoint to claim vouchers for a household."""
    data = request.get_json()

    household_id = data.get('household_id')
    nric = data.get('nric')

    # Validate required fields
    if not household_id or not nric:
        return jsonify({
            'status': 'error',
            'message': 'Missing required fields: household_id, nric'
        }), 400

    # Check if household exists
    if household_id not in users.keys():
        return jsonify({
            'status': 'error',
            'message': 'Household not found'
        }), 404

    household = users[household_id]
    stored_nric = household.get('nric', '')

    # Verify NRIC
    if stored_nric != nric.upper():
        return jsonify({
            'status': 'error',
            'message': 'NRIC verification failed'
        }), 403

    # Console echo
    print(f'''
          Function: API Claim Voucher
          Household ID: {household_id}
          Name: {household.get('name')} (NRIC: {nric})
          Status: Success
          Response: Voucher claim request processed via API.
          ''')

    return jsonify({
        'status': 'success',
        'message': 'Voucher claim request processed successfully',
        'household_id': household_id,
        'name': household.get('name'),
        'nric': nric,
        'voucher_value': 300,
        'voucher_breakdown': {
            '$2_vouchers': 30,
            '$5_vouchers': 12,
            '$10_vouchers': 15
        }
    }), 200
