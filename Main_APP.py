from flask import Flask, jsonify, render_template, redirect, url_for, request, session
import os
import subprocess
import sys
from datetime import datetime

# Import merchant blueprint and loader functions
from Merchant_api import merchant_bp, load_merchant_data
from Bank_api import bank_bp, load_bank_directory

# Import household blueprint and loader function
from House_Registration import household_bp, load_household_data

# Import voucher claim API blueprint
from Voucher_claim_api import voucher_claim_bp

# Import redemption modules
from algorithm_avl_greedy import process_reimbursement_avlgreedy_main
import redemption_tracker

# Initialize Flask application
app = Flask(__name__)

# Configure secret key for session management
app.config['SECRET_KEY'] = 'password123'

# Admin password
ADMIN_PASSWORD = 'Admin'

# Data and output folders
DATA_FOLDER = "."
TRANS_FOLDER = "transaction"
OUTPUT_FOLDER = "redeem_output"

# Register API blueprints
app.register_blueprint(bank_bp)
app.register_blueprint(merchant_bp)
app.register_blueprint(household_bp, url_prefix='/household') 

# register voucher claim API routes: /api/voucher/claim
app.register_blueprint(voucher_claim_bp)

# Route for the main page
@app.route('/')
def index():
    return render_template('index.html')

@app.route("/main",methods=["GET","POST"])
def main():
    return(render_template("main.html"))

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.clear()
    return redirect(url_for('index'))


# Route for household registration
@app.route('/household', methods=['GET', 'POST'])
def household():
    if request.method == 'POST':
        # Redirect to household registration page
        return redirect(url_for('household.registerPage'))
    # For GET requests, also redirect to registration
    return redirect(url_for('household.registerPage'))

# Route for merchant registration
@app.route('/merchant', methods=['GET', 'POST'])
def merchant():
    if request.method == 'POST':
        return redirect(url_for('merchant_register_page'))
    return redirect(url_for('merchant_register_page'))

@app.route('/merchant/register', methods=['GET'])
def merchant_register_page():
    return render_template('merchant_register.html')

# Voucher claim page
@app.route('/claim', methods=['GET', 'POST'])
def claim():
    return render_template('voucher_claim.html')

# Route for voucher consumption - Launch Flet mobile app directly
@app.route('/consume', methods=['GET', 'POST'])
def consume():
    """
    Launch the Flet mobile app for voucher consumption
    """
    if request.method == 'POST':
        try:
            # Launch mobile_app.py as a separate process immediately
            subprocess.Popen(
                [sys.executable, "mobile_app.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0
            )
            
            # Show success message and redirect back to main
            return render_template('consume_launched.html')
            
        except Exception as e:
            return f"<h1>Error</h1><p>Failed to launch mobile app: {str(e)}</p><a href='/main'>Back to Main</a>"
    
    return redirect(url_for('main'))

# Route to show admin login page
@app.route('/redemption', methods=['GET', 'POST'])
def redemption():
    """
    Show admin login page for redemption access
    """
    if request.method == 'POST':
        return render_template('admin_login.html')
    return render_template('admin_login.html')

# Route to verify admin password
@app.route('/verify_admin', methods=['POST'])
def verify_admin():
    password = request.form.get('password')
    
    # Check if password matches
    if password == ADMIN_PASSWORD:
        # Password is correct - set session flag
        session['admin_authenticated'] = True
        return redirect(url_for('admin_redemption'))
    else:
        # Password is incorrect - show error
        return render_template('admin_login.html', error='Incorrect password. Please try again.')

# Route for actual admin redemption page (protected)
@app.route('/admin_redemption')
def admin_redemption():
    """
    Admin redemption page - only accessible after password verification
    """
    # Check if admin is authenticated
    if not session.get('admin_authenticated'):
        return redirect(url_for('redemption'))
    
    # Get last redemption info
    last_redemption = redemption_tracker.get_last_redemption_info()
    
    # Render redemption form page
    return render_template('admin_redemption.html', last_redemption=last_redemption)

# API endpoint to process redemption
@app.route('/api/process_redemption', methods=['POST'])
def api_process_redemption():
    """
    API endpoint to process redemption request
    """
    # Check authentication
   # if not session.get('admin_authenticated'):
   #     return jsonify({
   #         'status': 'error',
   #         'message': 'Unauthorized access'
   #     }), 401
    
    # Get form data
    data = request.get_json()
    reimburse_date = data.get('reimburse_date')  # YYYYMMDD format
    start_hour = data.get('start_hour')  # 0-23
    end_hour = data.get('end_hour')  # 0-24
    
    # Validate inputs
    if not reimburse_date or start_hour is None or end_hour is None:
        return jsonify({
            'status': 'error',
            'message': 'Missing required fields: reimburse_date, start_hour, end_hour'
        }), 400
    
    try:
        start_hour = int(start_hour)
        end_hour = int(end_hour)
    except ValueError:
        return jsonify({
            'status': 'error',
            'message': 'Invalid hour format. Hours must be integers (0-24)'
        }), 400
    
    # Validate hour range
    if not (0 <= start_hour <= 23 and 0 <= end_hour <= 24):
        return jsonify({
            'status': 'error',
            'message': 'Start hour must be between 0 and 23, end hour between 0 and 24'
        }), 400
    
    if start_hour >= end_hour:
        return jsonify({
            'status': 'error',
            'message': 'Start hour must be less than end hour'
        }), 400
    
    # Validate date format
    try:
        datetime.strptime(reimburse_date, '%Y%m%d')
    except ValueError:
        return jsonify({
            'status': 'error',
            'message': 'Invalid date format. Use YYYYMMDD (e.g., 20260124)'
        }), 400
    
    # Check for duplicate redemption
    is_duplicate, error_msg = redemption_tracker.check_duplicate_redemption(
        reimburse_date, start_hour, end_hour
    )
    
    if is_duplicate:
        return jsonify({
            'status': 'error',
            'message': error_msg
        }), 409
    
    # Process redemption
    try:
        generated_files = process_reimbursement_avlgreedy_main(
            reimburse_date=reimburse_date,
            current_run_hour=end_hour,  # Use end_hour as current run hour
            run_hour1=end_hour,
            run_hour2=start_hour,
            data_folder=DATA_FOLDER,
            output_folder=OUTPUT_FOLDER
        )
        
        # Record redemption in history
        redemption_tracker.add_redemption_record(
            reimburse_date,
            start_hour,
            end_hour,
            generated_files
        )
        
        return jsonify({
            'status': 'success',
            'message': f'Redemption processed successfully! Generated {len(generated_files)} file(s)',
            'files_generated': generated_files,
            'output_folder': f'{OUTPUT_FOLDER}/{reimburse_date}/'
        }), 200
        
    except FileNotFoundError as e:
        return jsonify({
            'status': 'error',
            'message': f'Required data files not found: {str(e)}'
        }), 404
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error during processing: {str(e)}'
        }), 500

# Run the application
if __name__ == '__main__':
    # Load bank directory and merchant data on startup
    load_household_data()
    load_bank_directory()
    load_merchant_data()
    
    # Create necessary folders
    os.makedirs(DATA_FOLDER, exist_ok=True)
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    # Set debug=False for production
    app.run(debug=False, host='0.0.0.0', port=8000)
