from flask import Flask, render_template, request, redirect, url_for, session
from technician_service import assign_technician, update_technician_ratings
from db import get_db_connection

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Required for session management

# Mock user data - replace with your actual user authentication
users = {
    'TEN001': {'name': 'John Doe', 'property_id': 'PROP001'},
    'TEN002': {'name': 'Jane Smith', 'property_id': 'PROP002'}
}

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        tenant_id = request.form['tenant_id']
        if tenant_id in users:
            session['tenant_id'] = tenant_id
            return redirect(url_for('tenant_dashboard'))
        return "Invalid Tenant ID", 401
    return render_template('login.html')

@app.route('/tenant/dashboard')
def tenant_dashboard():
    if 'tenant_id' not in session:
        return redirect(url_for('login'))
    
    tenant_id = session['tenant_id']
    tenant_name = users[tenant_id]['name']
    
    # Get tenant's existing requests
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT * FROM MaintenanceRequests
            WHERE TenantID = %s
            ORDER BY CreatedAt DESC
        """, (tenant_id,))
        requests = cursor.fetchall()
    
    return render_template(
        'tenant_dashboard.html',
        tenant_name=tenant_name,
        requests=requests
    )

@app.route('/create_request', methods=['POST'])
def create_request():
    if 'tenant_id' not in session:
        return redirect(url_for('login'))
    
    try:
        request_data = {
            'tenant_id': session['tenant_id'],
            'skillset': request.form['skillset'],
            'description': request.form['description'],
            'zone': request.form['zone'],
            'urgency': int(request.form['urgency'])
        }
        
        # Assign technician and create request
        request_id = assign_technician(request_data)
        
        # Update all technician ratings
        update_technician_ratings()
        
        return redirect(url_for('request_confirmation', request_id=request_id))
    
    except Exception as e:
        return render_template('error.html', message=str(e))

@app.route('/confirmation/<int:request_id>')
def request_confirmation(request_id):
    if 'tenant_id' not in session:
        return redirect(url_for('login'))
    
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT mr.*, u.FirstName, u.LastName
            FROM MaintenanceRequests mr
            JOIN Technicians t ON mr.TechnicianID = t.TechnicianID
            JOIN Users u ON t.UserID = u.UserID
            WHERE mr.RequestID = %s
        """, (request_id,))
        request_info = cursor.fetchone()
    
    return render_template('confirmation.html', request=request_info)

@app.route('/logout')
def logout():
    session.pop('tenant_id', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)