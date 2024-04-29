import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from datetime import datetime


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static','uploads')
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['CKEDITOR_SERVE_LOCAL'] = True


db = SQLAlchemy(app)

class ServiceName(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    service_name = db.Column(db.String(100), nullable=False)
    service_description = db.Column(db.Text, nullable=True)
    screens = db.relationship('Screen', backref='service', lazy=True)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    user_description = db.Column(db.Text, nullable=True)

    # Define many-to-many relationship with Screen model
    screens = db.relationship('Screen', secondary='screen_user', backref='users')

class Screen(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    screen_name = db.Column(db.String(100), nullable=False)
    screen_description = db.Column(db.Text, nullable=True)
    screenshot_path = db.Column(db.String(255), nullable=True)
    service_id = db.Column(db.Integer, db.ForeignKey('service_name.id'), nullable=False)
    service_description = db.Column(db.Text, nullable=True)
    table_id = db.Column(db.Integer, db.ForeignKey('table.id'), nullable=True)

class Table(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    table_name = db.Column(db.String(100), nullable=False)
    table_description = db.Column(db.Text, nullable=True)
    screens = db.relationship('Screen', backref='table', lazy=True)

# Define association table for many-to-many relationship between Screen and User
screen_user = db.Table('screen_user',
    db.Column('screen_id', db.Integer, db.ForeignKey('screen.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)

# Create the database tables
with app.app_context():
    db.create_all()

# Route to render the homepage template and pass data to it
@app.route('/addscreens')
def addscreens():
    table_id = request.args.get('table_id')
    # Fetch table details based on table_id
    table = Table.query.get(table_id)
    # Fetch other necessary data like services and users
    services = ServiceName.query.all()
    users = User.query.all()
    # Pass the table_id, services, and users to the template
    return render_template('addscreens.html', table_id=table_id, services=services, users=users)


@app.route('/service/<service_name>')
def get_service_description(service_name):
    service = ServiceName.query.filter_by(service_name=service_name).first()
    if service:
        return jsonify({'service_description': service.service_description})
    else:
        return jsonify({'error': 'Service not found'}), 404


@app.route('/add_user', methods=['POST'])
def add_user():
    if request.method == 'POST':
        # Retrieve data from the form fields
        username = request.form['username']
        user_description = request.form['user_description']
        
        # Create a new user object
        new_user = User(username=username, user_description=user_description)
        
        # Add the new user to the database
        db.session.add(new_user)
        db.session.commit()  # Commit the transaction
        
        flash('User added successfully', 'success')
        return redirect('/users')
    else:
        return 'Method not allowed'

@app.route('/add_service', methods=['POST'])
def add_service():
    if request.method == 'POST':
        # Retrieve data from the form fields
        service_name = request.form['service_name']
        service_description = request.form['service_description']
        
        # Create a new service object
        new_service = ServiceName(service_name=service_name, service_description=service_description)
        
        # Add the new service to the database
        db.session.add(new_service)
        db.session.commit()  # Commit the transaction
        
        flash('Service added successfully', 'success')
        return redirect('/services')
    else:
        return 'Method not allowed'

@app.route('/')
def display_tables():
    tables = Table.query.all()
    return render_template('tables.html', tables=tables)

from flask import render_template

@app.route('/table/<int:table_id>')
def table_details(table_id):
    table = Table.query.get(table_id)
    service_name = None
    service_description = None
    users = set()
    for screen in table.screens:
        for user in screen.users:
            users.add(user)
    if table.screens:
        # If there are screens associated with the table, get the service name from the first screen
        screen = table.screens[0]
        service_name = screen.service.service_name
        # Fetch service description based on service name
        service_description = ServiceName.query.filter_by(service_name=service_name).first().service_description

    return render_template('table_details.html', table=table, users=users,  service_name=service_name, service_description=service_description)
@app.route('/print/<int:table_id>')
def print(table_id):
    table = Table.query.get_or_404(table_id)
    service_name = None
    service_description = None
    if table.screens:
        # If there are screens associated with the table, get the service name from the first screen
        screen = table.screens[0]
        service_name = screen.service.service_name
        # Fetch service description based on service name
        service_description = ServiceName.query.filter_by(service_name=service_name).first().service_description
        users = User.query.all()
    return render_template('print.html', table=table, service_name=service_name, service_description=service_description,users=users)



@app.route('/add_screen_to_table/wireframe.html')
def wireframetool():
    return render_template('wireframe.html')
@app.route('/new_table')
def new_table_form():
    return render_template('new_table.html')

@app.route('/create_table', methods=['POST'])
def create_table():
    if request.method == 'POST':
        table_name = request.form['table_name']
        table_description = request.form['table_description']
        
        # Create a new table object
        new_table = Table(table_name=table_name, table_description=table_description)
        
        # Add the new table to the database
        db.session.add(new_table)
        db.session.commit()
        
        # Redirect the user to the tables page
        return redirect('/')
@app.route('/users')
def users():
    # Fetch data from the database
    services = ServiceName.query.all()
    users = User.query.all()
    
    # Render the template and pass the data to it
    return render_template('users.html', services=services, users=users)


@app.route('/services')
def services():
    # Fetch data from the database
    services = ServiceName.query.all()
    users = User.query.all()
    
    # Render the template and pass the data to it
    return render_template('services.html', services=services, users=users)

@app.route('/userlist')
def userlist():
    # Fetch data from the database
    services = ServiceName.query.all()
    users = User.query.all()
    
    # Render the template and pass the data to it
    return render_template('userlist.html', services=services, users=users)
@app.route('/servicelist')
def servicelist():
    # Fetch data from the database
    services = ServiceName.query.all()
    users = User.query.all()
    
    # Render the template and pass the data to it
    return render_template('servicelist.html', services=services, users=users)
from flask import flash

@app.route('/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    
    # Check if the user has associated screens
    if user.screens:
        flash('اسم المستخدم مستعمل داخل شاشة في احد الجداول لا يمكن حذفه', 'error')
        return redirect('/userlist')
    
    # Delete the user from the database
    db.session.delete(user)
    db.session.commit()

    flash('User deleted successfully', 'success')
    return redirect('/userlist')

@app.route('/delete_service/<int:service_id>', methods=['POST'])
def delete_service(service_id):
    service = ServiceName.query.get_or_404(service_id)
    
    # Check if the service has associated screens
    if service.screens:
        flash('الخدمة مستعملة داخل شاشة في احد الجداول لا يمكن حذفها', 'error')
        return redirect('/servicelist')
    
    # Delete the service from the database
    db.session.delete(service)
    db.session.commit()

    flash('Service deleted successfully', 'success')
    return redirect('/servicelist')

@app.route('/delete_screen/<int:screen_id>', methods=['POST'])
def delete_screen(screen_id):
    # Get the screen from the database
    screen = Screen.query.get_or_404(screen_id)
    
    # Fetch the table_id associated with the screen
    table_id = screen.table_id
    
    # Delete the file from the server if it exists
    if screen.screenshot_path:
        try:
            os.remove(os.path.join(app.root_path, 'static/uploads', screen.screenshot_path))
        except FileNotFoundError:
            pass
    
    # Delete the screen from the database
    db.session.delete(screen)
    db.session.commit()

    flash('Screen deleted successfully', 'success')
    
    # Redirect to the table page associated with the deleted screen
    return redirect(f'/table/{table_id}')


@app.route('/user/<int:user_id>')
def get_user_description(user_id):
    user = User.query.get(user_id)
    if user:
        return jsonify({'user_description': user.user_description}), 200
    else:
        return jsonify({'error': 'User not found'}), 404
    
@app.route('/details/<int:screen_id>')
def show_screen_details(screen_id):
    screen = Screen.query.get(screen_id)
    if screen:
        return render_template('details.html', screen=screen)
    else:
        flash('Screen not found', 'error')
        return redirect(url_for('display_screens'))
    
@app.route('/update_screen/<int:screen_id>', methods=['POST'])
def update_screen(screen_id):
    if request.method == 'POST':
        # Retrieve the updated screen details from the form
        screen = Screen.query.get(screen_id)
        if screen:
            screen.screen_name = request.form['screen_name']
            screen.user_description = request.form['user_description']
            screen.service_description = request.form['service_description']
            
            # Commit the changes to the database
            db.session.commit()
            
            flash('Screen details updated successfully', 'success')
        else:
            flash('Screen not found', 'error')
        
        # Redirect the user back to the details page
        return redirect(url_for('show_screen_details', screen_id=screen_id))
    else:
        # Handle invalid HTTP method
        return 'Method not allowed', 405

@app.route('/table/<int:table_id>')
def table(table_id):
    # Fetch screens related to the specified table
    
    table = Table.query.get(table_id)
    if table:
        screens = table.screens
        return render_template('table.html',screens=screens)
    else:
        flash('Table not found', 'error')
        return redirect(url_for('display_screens'))

@app.route('/add_screen_to_table/<int:table_id>')
def add_screen_to_table_form(table_id):
    users = User.query.all()
    services = ServiceName.query.all()
    return render_template('add_screen_to_table.html', table_id=table_id, users=users, services=services)

@app.route('/delete_table/<int:table_id>', methods=['POST'])
def delete_table(table_id):
    table = Table.query.get_or_404(table_id)
    
    # Iterate over the screens associated with the table
    for screen in table.screens:
        # Delete the associated image file from the server, if it exists
        if screen.screenshot_path:
            try:
                os.remove(os.path.join(app.root_path, 'static/uploads', screen.screenshot_path))
            except FileNotFoundError:
                pass
    
    # Delete associated screens
    for screen in table.screens:
        db.session.delete(screen)

    # Delete the table itself
    db.session.delete(table)
    db.session.commit()

    flash('Table and associated screens deleted successfully', 'success')
    return redirect('/')


from flask import request, redirect, flash

@app.route('/create_screen_for_table', methods=['POST'])
def create_screen_for_table():
    if request.method == 'POST':
        # Retrieve form data
        screen_name = request.form['screen_name']
        screen_description = request.form['screen_description']
        service_name = request.form['service_name']
        table_id = request.form['table_id']
        user_ids = request.form.getlist('user_ids')  # Retrieve multiple user IDs
        
        # Retrieve the service
        service = ServiceName.query.filter_by(service_name=service_name).first()

        if not service:
            flash('Service not found', 'error')
            return redirect(request.url)

        # Handle file upload
        if 'screenshot_path' not in request.files:
            flash('No file part', 'error')
            return redirect(request.url)

        screenshot_file = request.files['screenshot_path']
        if screenshot_file.filename == '':
            flash('No selected file', 'error')
            return redirect(request.url)

        if screenshot_file:
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            file_extension = screenshot_file.filename.split('.')[-1]
            filename = f"{secure_filename(screenshot_file.filename)}_{timestamp}.{file_extension}"
            screenshot_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            screenshot_file.save(screenshot_path)
        else:
            screenshot_path = None

        # Create a new screen
        new_screen = Screen(
            screen_name=screen_name,
            screen_description=screen_description,
            screenshot_path=filename,
            service_id=service.id,
            table_id=table_id
        )

        # Add the selected users to the screen
        for user_id in user_ids:
            user = User.query.get(user_id)
            if user:
                new_screen.users.append(user)

        db.session.add(new_screen)
        db.session.commit()

        flash('Screen added successfully', 'success')
        return redirect(f'/table/{table_id}')
    else:
        flash('Method not allowed', 'error')
        return redirect('/')




from flask import request


@app.route('/edit_screen/<int:screen_id>', methods=['GET', 'POST'])
def edit_screen(screen_id):
    screen = Screen.query.get_or_404(screen_id)
    users = User.query.all()
    services = ServiceName.query.all()
    
    if request.method == 'POST':
        # Retrieve form data
        screen.screen_name = request.form['screen_name']
        screen.screen_description = request.form['screen_description']
        # Retrieve selected user IDs as a list
        selected_user_ids = request.form.getlist('user_ids')
        # Convert the list of strings to integers
        selected_user_ids = [int(user_id) for user_id in selected_user_ids]
        # Update the association between screen and users
        screen.users = User.query.filter(User.id.in_(selected_user_ids)).all()
        screen.service_id = request.form['service_id']
        
        db.session.commit()
        
        flash('Screen details updated successfully', 'success')
        
        # Redirect back to the table page associated with the screen
        return redirect(f'/table/{screen.table_id}')
    
    return render_template('edit_screen.html', screen=screen, users=users, services=services)
@app.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        # Retrieve form data
        user.username = request.form['username']
        user.user_description = request.form['user_description']
        
        db.session.commit()
        
        flash('User details updated successfully', 'success')
        
        # Redirect back to the user list page
        return redirect('/userlist')
    
    return render_template('edit_user.html', user=user)


if __name__ == '__main__':
    app.run(debug=True)
