import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from datetime import datetime
import shutil


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static','uploads')
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['CKEDITOR_SERVE_LOCAL'] = True

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    user_description = db.Column(db.Text, nullable=True)
    screens = db.relationship('Screen', secondary='screen_user', backref='users')

class Screen(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    screen_name = db.Column(db.String(100), nullable=False)
    screen_description = db.Column(db.Text, nullable=True)
    screenshot_path = db.Column(db.String(255), nullable=True)
    table_id = db.Column(db.Integer, db.ForeignKey('table.id'), nullable=True)



class Table(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    table_name = db.Column(db.String(100), nullable=False)
    table_description = db.Column(db.Text, nullable=True)
    sector_class = db.Column(db.Text, nullable=True)
    service_place = db.Column(db.Text, nullable=True)
    service_structure = db.Column(db.Text, nullable=True)
    service_type = db.Column(db.Text, nullable=True)
    service_class = db.Column(db.Text, nullable=True)
    fees = db.Column(db.Text, nullable=True)
    fees_description = db.Column(db.Text, nullable=True)
    fees_amount = db.Column(db.Integer, nullable=True)
    fees_payment = db.Column(db.Text, nullable=True)
    general_rules = db.Column(db.Text, nullable=True)
    customer_category = db.Column(db.Text, nullable=True)
    document_name = db.Column(db.Text, nullable=True)
    document_type = db.Column(db.Text, nullable=True)
    document_description = db.Column(db.Text, nullable=True)
    document_rules = db.Column(db.Text, nullable=True)
    document_origin = db.Column(db.Text, nullable=True) 
    outputs_name = db.Column(db.Text, nullable=True)
    outputs_type = db.Column(db.Text, nullable=True)
    outputs_description = db.Column(db.Text, nullable=True)  
    outputs_rules = db.Column(db.Text, nullable=True) 
    outputs_expiry = db.Column(db.Text, nullable=True)
    screens = db.relationship('Screen', backref='table', lazy=True)

    # Define a many-to-many relationship with ServiceChannel
    channels = db.relationship('ServiceChannel', secondary='table_channel', backref='tables')

    # Define a many-to-many relationship with ServiceBeneficiary
    beneficiaries = db.relationship('ServiceBeneficiary', secondary='table_beneficiary', backref='tables')


# Define association table for many-to-many relationship between Table and ServiceChannel
table_channel = db.Table('table_channel',
    db.Column('table_id', db.Integer, db.ForeignKey('table.id'), primary_key=True),
    db.Column('channel_id', db.Integer, db.ForeignKey('service_channel.id'), primary_key=True)
)

# Define association table for many-to-many relationship between Table and ServiceBeneficiary
table_beneficiary = db.Table('table_beneficiary',
    db.Column('table_id', db.Integer, db.ForeignKey('table.id'), primary_key=True),
    db.Column('beneficiary_id', db.Integer, db.ForeignKey('service_beneficiary.id'), primary_key=True)
)

screen_user = db.Table('screen_user',
    db.Column('screen_id', db.Integer, db.ForeignKey('screen.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)
class ServiceChannel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    channel_name = db.Column(db.String(100), nullable=False)

class ServiceBeneficiary(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    beneficiary_name = db.Column(db.String(100), nullable=False)
# Create the database tables

class UserDescription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    table_id = db.Column(db.Integer, db.ForeignKey('table.id'), nullable=False)    

with app.app_context():
    db.create_all()

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
        
       
        return redirect('/users')
    else:
        return 'Method not allowed'

@app.route('/add_service', methods=['POST'])
def add_service():
    if request.method == 'POST':
        # Retrieve data from the form fields
        service_name = request.form['service_name']
        service_description = request.form['service_description']
        return redirect('/services')
    else:
        return 'Method not allowed'

@app.route('/')
def display_tables():
    tables = Table.query.all()
    return render_template('tables.html', tables=tables)



@app.route('/table/<int:table_id>')
def table_details(table_id):
    table = Table.query.get(table_id)
    
    # Fetch users connected to screens added
    users = User.query.filter(User.screens.any(table_id=table_id)).all()
    
    user_descriptions = {}  # Create an empty dictionary to store user descriptions
    
    # Fetch user descriptions related to the specified table_id
    for user in users:
        user_description = UserDescription.query.filter_by(user_id=user.id, table_id=table_id).first()
        if user_description:
            user_descriptions[user.id] = user_description.description
    
    return render_template('table_details.html', table=table, users=users, user_descriptions=user_descriptions)






@app.route('/wireframe.html')
def wireframetool():
    return render_template('wireframe.html')

@app.route('/new_table')
def new_table_form():
    channels = ServiceChannel.query.all()
    beneficiaries = ServiceBeneficiary.query.all()
    return render_template('new_table.html', channels=channels, beneficiaries=beneficiaries)

@app.route('/create_table', methods=['POST'])
def create_table():
    # Retrieve form data
    table_name = request.form['table_name']
    table_description = request.form['table_description']
    sector_class = request.form['sector_class']
    service_type = request.form.get('service_type')
    service_place = request.form.get('service_place')
    service_structure = request.form.get('service_structure')
    service_class = request.form.get('service_class')
    fees = request.form.get('fees')
    fees_description = request.form.get('fees_description')
    fees_amount = request.form.get('fees_amount')
    fees_payment = request.form.get('fees_payment')
    general_rules = request.form.get('general_rules')
    customer_category = request.form.get('customer_category')
    document_name = request.form.get('document_name')
    document_type = request.form.get('document_type')
    document_description = request.form.get('document_description')
    document_rules = request.form.get('document_rules')
    document_origin = request.form.get('document_origin')
    outputs_name = request.form.get('outputs_name')
    outputs_type = request.form.get('outputs_type')
    outputs_description = request.form.get('outputs_description')
    outputs_rules = request.form.get('outputs_rules')
    outputs_expiry = request.form.get('outputs_expiry')
    channels_selected = request.form.getlist('channels')
    beneficiaries_selected = request.form.getlist('beneficiaries')
    
    # Create a new table instance
    new_table = Table(
        table_name=table_name,
        table_description=table_description,
        sector_class=sector_class,
        service_type=service_type,
        service_place=service_place,
        service_structure=service_structure,
        service_class=service_class,
        fees=fees,
        fees_description=fees_description,
        fees_amount=fees_amount,
        fees_payment=fees_payment,
        general_rules=general_rules,
        customer_category=customer_category,
        document_name=document_name,
        document_type=document_type,
        document_description=document_description,
        document_rules=document_rules,
        document_origin=document_origin,
        outputs_name=outputs_name,
        outputs_type=outputs_type,
        outputs_description=outputs_description,
        outputs_rules=outputs_rules,
        outputs_expiry=outputs_expiry
    )
    
    # Add the new table to the database and commit to generate the ID
    db.session.add(new_table)
    db.session.commit()
    
    # Associate selected channels with the new table
    for channel_id in channels_selected:
        channel = ServiceChannel.query.get(channel_id)
        if channel:
            new_table.channels.append(channel)
    
    # Associate selected beneficiaries with the new table
    for beneficiary_id in beneficiaries_selected:
        beneficiary = ServiceBeneficiary.query.get(beneficiary_id)
        if beneficiary:
            new_table.beneficiaries.append(beneficiary)
    
    # Commit the associations
    db.session.commit()
    
    # Redirect to the screen creation page for the new table
    return redirect(f'/add_screen_to_table/{new_table.id}')






@app.route('/users')
def users():
    # Fetch data from the database
    users = User.query.all()
    # Render the template and pass the data to it
    return render_template('users.html', users=users)




@app.route('/userlist')
def userlist():
    # Fetch data from the database
    # services = ServiceName.query.all()
    users = User.query.all()
    
    # Render the template and pass the data to it
    return render_template('userlist.html', users=users)

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

    
    
    # Redirect to the table page associated with the deleted screen
    return redirect(f'/table/{table_id}')

    

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
   
    return render_template('add_screen_to_table.html', table_id=table_id, users=users)

@app.route('/delete_table/<int:table_id>', methods=['POST'])
def delete_table(table_id):
    table = Table.query.get_or_404(table_id)
    
    # Delete associated UserDescription records
    user_descriptions = UserDescription.query.filter_by(table_id=table_id).all()
    for user_description in user_descriptions:
        db.session.delete(user_description)
    
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

    return redirect('/')

    

@app.route('/create_screen_for_table', methods=['POST'])
def create_screen_for_table():
    if request.method == 'POST':
        # Retrieve form data
        screen_name = request.form['screen_name']
        screen_description = request.form['screen_description']
        table_id = request.form['table_id']
        user_ids = request.form.getlist('user_ids')  # Retrieve multiple user IDs
        
        # Handle file upload
        if 'screenshot_path' not in request.files:
            return redirect(request.url)

        screenshot_file = request.files['screenshot_path']
        if screenshot_file.filename == '':
            return redirect(request.url)

        # Save the original file
        original_timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        file_extension = screenshot_file.filename.split('.')[-1]
        original_filename = secure_filename(screenshot_file.filename)
        original_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{original_filename}_{original_timestamp}.{file_extension}")
        screenshot_file.save(original_path)

        # Create a screen for each user
        for user_id in user_ids:
            user_timestamp = datetime.now().strftime("%Y%m%d%H%M%S_%f")
            user_filename = f"{secure_filename(screenshot_file.filename)}_{user_timestamp}.{file_extension}"
            user_path = os.path.join(app.config['UPLOAD_FOLDER'], user_filename)

            # Copy the original file for the user
            shutil.copyfile(original_path, user_path)

            new_screen = Screen(
                screen_name=screen_name,
                screen_description=screen_description,
                screenshot_path=user_filename,
                table_id=table_id
            )
            
            user = User.query.get(user_id)
            if user:
                new_screen.users.append(user)
            
            db.session.add(new_screen)

        db.session.commit()

        return redirect(f'/table/{table_id}')
    else:
        return redirect('/')




from flask import request


@app.route('/edit_screen/<int:screen_id>', methods=['GET', 'POST'])
def edit_screen(screen_id):
    screen = Screen.query.get_or_404(screen_id)
    users = User.query.all()
    
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
    
        db.session.commit()
        
        # Redirect back to the table page associated with the screen
        return redirect(f'/table/{screen.table_id}')
    
    return render_template('edit_screen.html', screen=screen, users=users)
@app.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        # Retrieve form data
        user.username = request.form['username']
        user.user_description = request.form['user_description']
        
        db.session.commit()
        
      
        
        # Redirect back to the user list page
        return redirect('/userlist')
    
    return render_template('edit_user.html', user=user)
@app.route('/add_service_channel', methods=['POST'])
def add_service_channel():
    if request.method == 'POST':
        channel_name = request.form['channel_name']
        
        # Create a new service channel object
        new_channel = ServiceChannel(channel_name=channel_name)
        
        # Add the new channel to the database
        db.session.add(new_channel)
        db.session.commit()
        
        
        return redirect('/add_service_channel_form')
    else:
        return 'Method not allowed'

# Method to add a new service beneficiary
@app.route('/add_service_beneficiary', methods=['POST'])
def add_service_beneficiary():
    if request.method == 'POST':
        beneficiary_name = request.form['beneficiary_name']
        
        # Create a new service beneficiary object
        new_beneficiary = ServiceBeneficiary(beneficiary_name=beneficiary_name)
        
        # Add the new beneficiary to the database
        db.session.add(new_beneficiary)
        db.session.commit()
        
        
        return redirect('/add_service_beneficiary_form')
    else:
        return 'Method not allowed'
@app.route('/add_service_channel_form', methods=['GET'])
def add_service_channel_form():
    return render_template('service_channel_form.html')

@app.route('/add_service_beneficiary_form', methods=['GET'])
def add_service_beneficiary_form():
    return render_template('service_beneficiary_form.html')
@app.route('/channels')
def show_all_channels():
    channels = ServiceChannel.query.all()
    return render_template('channels.html', channels=channels)

# Route to handle the deletion of a channel
@app.route('/delete_channel/<int:channel_id>', methods=['POST'])
def delete_channel(channel_id):
    channel = ServiceChannel.query.get_or_404(channel_id)
    try:
        db.session.delete(channel)
        db.session.commit()
       
    except:
        db.session.rollback()
        
    finally:
        db.session.close()
    return redirect(url_for('show_all_channels'))
# Route to render the HTML page showing all beneficiaries
@app.route('/beneficiaries')
def show_all_beneficiaries():
    beneficiaries = ServiceBeneficiary.query.all()
    return render_template('beneficiaries.html', beneficiaries=beneficiaries)

# Route to handle the deletion of a beneficiary
@app.route('/delete_beneficiary/<int:beneficiary_id>', methods=['POST'])
def delete_beneficiary(beneficiary_id):
    beneficiary = ServiceBeneficiary.query.get_or_404(beneficiary_id)
    try:
        db.session.delete(beneficiary)
        db.session.commit()
       
    except:
        db.session.rollback()
        
    finally:
        db.session.close()
    return redirect(url_for('show_all_beneficiaries'))
@app.route('/table_info/<int:table_id>')
def table_info(table_id):
    # Query the database to fetch the data for the specified table_id
    table = Table.query.get(table_id)
    
    # Render the template and pass the data to it
    return render_template('table_info.html', table=table)

@app.route('/save_user_descriptions', methods=['POST'])
def save_user_descriptions():
    if request.method == 'POST':
        # Retrieve form data
        table_id = request.form['table_id']
        user_descriptions = request.form.getlist('user_descriptions[]')

        # Retrieve users associated with the specified table
        users = User.query.join(screen_user).join(Screen).filter(Screen.table_id == table_id).all()

        # Loop through users and update their descriptions
        for user, description in zip(users, user_descriptions):
            user_description = UserDescription.query.filter_by(user_id=user.id, table_id=table_id).first()
            if user_description:
                # If a description exists, update it
                user_description.description = description
            else:
                # If no description exists, create a new UserDescription object
                user_description = UserDescription(user_id=user.id, table_id=table_id, description=description)
                db.session.add(user_description)

        db.session.commit()

        # Redirect back to the table details page
        return redirect(f'/table/{table_id}')
    else:
        # Handle other HTTP methods if necessary
        return 'Method not allowed'

@app.route('/print/<int:table_id>')
def print(table_id):
    table = Table.query.get(table_id)
    
    # Fetch only the screens related to the specified table_id
    screens = Screen.query.filter_by(table_id=table_id).all()
    
    # Fetch users connected to screens added
    users = User.query.filter(User.screens.any(table_id=table_id)).all()
    
    user_descriptions = {}  # Create an empty dictionary to store user descriptions
    
    # Fetch user descriptions related to the specified table_id
    for user in users:
        user_description = UserDescription.query.filter_by(user_id=user.id, table_id=table_id).first()
        if user_description:
            user_descriptions[user.id] = user_description.description
    
    return render_template('print.html', table=table, screens=screens, users=users, user_descriptions=user_descriptions)


@app.route('/update_table_info/<int:table_id>', methods=['POST'])
def update_table_info(table_id):
    # Retrieve the table from the database
    table = Table.query.get(table_id)

    # Update the table information based on the form data
    table.table_name = request.form['table_name']
    table.sector_class = request.form['sector_class']
    table.service_place = request.form['service_place']
    table.service_structure = request.form['service_structure']
    table.service_type = request.form['service_type']
    table.service_class = request.form['service_class']
    table.fees = request.form['fees']
    table.fees_description = request.form['fees_description']
    table.fees_amount = request.form['fees_amount']
    table.fees_payment = request.form['fees_payment']
    table.general_rules = request.form['general_rules']
    table.customer_category = request.form['customer_category']
    table.document_name = request.form['document_name']
    table.document_type = request.form['document_type']
    table.document_description = request.form['document_description']
    table.document_rules = request.form['document_rules']
    table.document_origin = request.form['document_origin']
    table.outputs_name = request.form['outputs_name']
    table.outputs_type = request.form['outputs_type']
    table.outputs_description = request.form['outputs_description']
    table.outputs_rules = request.form['outputs_rules']
    table.outputs_expiry = request.form['outputs_expiry']

    # Commit the changes to the database
    db.session.commit()

    # Redirect to the table details page after updating the information
    return redirect(url_for('table_details', table_id=table_id))

if __name__ == '__main__':
    app.run(debug=True)
