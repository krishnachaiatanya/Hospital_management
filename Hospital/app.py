from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from sqlalchemy import text, inspect
import os
from dotenv import load_dotenv
import os.path

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key')

# Use an absolute path for SQLite database
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(basedir, 'hospital.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class Patient(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    phone_number = db.Column(db.String(20))
    is_admin = db.Column(db.Boolean, default=False)
    appointments = db.relationship('Appointment', backref='patient', lazy=True)
    admissions = db.relationship('AdmittedPatient', backref='patient', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Doctor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    specialization = db.Column(db.String(100), nullable=False)
    qualifications = db.Column(db.String(200), nullable=False)
    years_of_experience = db.Column(db.Integer, nullable=False)
    appointments = db.relationship('Appointment', backref='doctor', lazy=True)
    date_slots = db.relationship('DateSpecificSlot', backref='doctor', lazy=True)
    admitted_patients = db.relationship('AdmittedPatient', backref='doctor', lazy=True)

class DateSpecificSlot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.String(5), nullable=False)  # Format: "HH:MM"
    end_time = db.Column(db.String(5), nullable=False)    # Format: "HH:MM"
    appointments_count = db.Column(db.Integer, default=0)
    is_available = db.Column(db.Boolean, default=True)
    appointments = db.relationship('Appointment', backref='date_specific_slot', lazy=True)

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    date_specific_slot_id = db.Column(db.Integer, db.ForeignKey('date_specific_slot.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.String(5), nullable=False)
    status = db.Column(db.String(20), default='pending')
    registered_by_admin = db.Column(db.Boolean, default=False)
    patient_name = db.Column(db.String(100))
    patient_email = db.Column(db.String(120))
    patient_age = db.Column(db.Integer)
    patient_gender = db.Column(db.String(10))
    department = db.Column(db.String(100))

class AdmittedPatient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=True)
    patient_name = db.Column(db.String(100), nullable=False)
    patient_age = db.Column(db.Integer, nullable=False)
    patient_gender = db.Column(db.String(10), nullable=False)
    room_number = db.Column(db.String(20), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    admission_date = db.Column(db.Date, nullable=False)
    discharge_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(20), default='admitted')  # admitted, discharged
    phone_number = db.Column(db.String(20))
    diagnosis = db.Column(db.String(200))
    notes = db.Column(db.Text)

@login_manager.user_loader
def load_user(user_id):
    return Patient.query.get(int(user_id))

def init_db():
    with app.app_context():
        # Create admin user if it doesn't exist
        admin = Patient.query.filter_by(username='admin').first()
        if not admin:
            admin = Patient(
                username='admin',
                email='admin@hospital.com',
                phone_number='0000000000',
                is_admin=True
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("Admin user created successfully!")
        
        # Add sample doctors if none exist
        if not Doctor.query.first():
            doctors = [
                Doctor(
                    name='Dr. John Smith',
                    specialization='Cardiology',
                    qualifications='MBBS, MD, DM',
                    years_of_experience=15
                ),
                Doctor(
                    name='Dr. Sarah Johnson',
                    specialization='Pediatrics',
                    qualifications='MBBS, MD',
                    years_of_experience=12
                ),
                Doctor(
                    name='Dr. Michael Brown',
                    specialization='Orthopedics',
                    qualifications='MBBS, MS',
                    years_of_experience=18
                ),
                Doctor(
                    name='Dr. Emily Davis',
                    specialization='Neurology',
                    qualifications='MBBS, MD, DM',
                    years_of_experience=14
                ),
                Doctor(
                    name='Dr. Robert Wilson',
                    specialization='Dermatology',
                    qualifications='MBBS, MD',
                    years_of_experience=10
                )
            ]
            for doctor in doctors:
                db.session.add(doctor)
            db.session.commit()
            print("Sample doctors added successfully!")

def recreate_db():
    with app.app_context():
        # Drop tables in the correct order
        db.session.execute(text('DROP TABLE IF EXISTS appointment'))
        db.session.execute(text('DROP TABLE IF EXISTS date_specific_slot'))
        db.session.execute(text('DROP TABLE IF EXISTS doctor_slot'))
        db.session.execute(text('DROP TABLE IF EXISTS doctor'))
        db.session.execute(text('DROP TABLE IF EXISTS patient'))
        db.session.commit()
        
        # Create all tables
        db.create_all()
        
        # Initialize the database
        init_db()
        
        print("Database recreated successfully!")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        phone_number = request.form['phone_number']
        
        if Patient.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('register'))
            
        if Patient.query.filter_by(email=email).first():
            flash('Email already registered')
            return redirect(url_for('register'))
            
        patient = Patient(username=username, email=email, phone_number=phone_number)
        patient.set_password(password)
        db.session.add(patient)
        db.session.commit()
        
        flash('Registration successful! Please login.')
        return redirect(url_for('login'))
        
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username_or_email = request.form.get('username')
        password = request.form.get('password')
        remember = 'remember' in request.form
        
        # Try to find user by username first
        patient = Patient.query.filter_by(username=username_or_email).first()
        
        # If not found, try to find by email
        if not patient:
            patient = Patient.query.filter_by(email=username_or_email).first()
        
        # Debug - print details about the login attempt
        print(f"Login attempt for: {username_or_email}")
        print(f"User found: {patient is not None}")
        
        if patient:
            # Check password
            password_correct = patient.check_password(password)
            print(f"Password check result: {password_correct}")
            
            if password_correct:
                login_user(patient, remember=remember)
                # Redirect to the page the user was trying to access
                next_page = request.args.get('next')
                if next_page:
                    return redirect(next_page)
                
                if patient.is_admin:
                    return redirect(url_for('admin_dashboard'))
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid password. Please try again.', 'danger')
        else:
            flash('User not found. Please check your username/email.', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    
    appointments = Appointment.query.filter_by(patient_id=current_user.id).all()
    
    # Get search parameters
    doctor_name = request.args.get('name', '')
    specialization = request.args.get('specialization', '')
    
    # Filter doctors based on search criteria
    doctors_query = Doctor.query
    
    if doctor_name:
        doctors_query = doctors_query.filter(Doctor.name.ilike(f'%{doctor_name}%'))
    
    if specialization:
        doctors_query = doctors_query.filter(Doctor.specialization == specialization)
    
    doctors = doctors_query.all()
    
    # Get unique specializations for the dropdown
    all_specializations = [doc.specialization for doc in Doctor.query.with_entities(Doctor.specialization).distinct()]
    
    now = datetime.now()
    return render_template('dashboard.html', 
                          appointments=appointments, 
                          doctors=doctors, 
                          now=now,
                          specializations=all_specializations)

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get patients (still needed for statistics)
    patients = Patient.query.filter_by(is_admin=False).all()
    
    # Get today's date for filtering
    today = datetime.now().date()
    now = datetime.now()
    
    # Get search parameters
    patient_name = request.args.get('patient_name', '')
    doctor_name = request.args.get('doctor_name', '')
    department = request.args.get('department', '')
    
    # Base query for today's appointments
    appointments_query = Appointment.query.filter(Appointment.date == today)
    
    # Apply filters if provided
    if patient_name:
        # Search by patient_name field or by username
        appointments_query = appointments_query.filter(
            db.or_(
                Appointment.patient_name.ilike(f'%{patient_name}%'),
                Appointment.patient.has(Patient.username.ilike(f'%{patient_name}%'))
            )
        )
    
    if doctor_name:
        # Search by doctor name
        appointments_query = appointments_query.filter(
            Appointment.doctor.has(Doctor.name.ilike(f'%{doctor_name}%'))
        )
    
    if department:
        # Search by department field or by doctor's specialization
        appointments_query = appointments_query.filter(
            db.or_(
                Appointment.department == department,
                Appointment.doctor.has(Doctor.specialization == department)
            )
        )
    
    # Get today's appointments with filters applied, ordered by time
    today_appointments = appointments_query.order_by(Appointment.time).all()
    
    # Count today's appointments for the stat card
    today_appointments_count = Appointment.query.filter(Appointment.date == today).count()
    
    # Count total pending appointments (for the Total Appointments stat card)
    total_pending_count = Appointment.query.filter(Appointment.status != 'completed').count()
    
    # Count currently admitted patients
    admitted_count = AdmittedPatient.query.filter_by(status='admitted').count()
    
    # Filter doctors based on search criteria for doctor section
    doctors_query = Doctor.query
    
    if doctor_name:
        doctors_query = doctors_query.filter(Doctor.name.ilike(f'%{doctor_name}%'))
    
    if department:
        doctors_query = doctors_query.filter(Doctor.specialization == department)
    
    doctors = doctors_query.all()
    
    # Get unique specializations for the dropdown
    all_specializations = [doc.specialization for doc in Doctor.query.with_entities(Doctor.specialization).distinct()]
    
    return render_template('admin_dashboard.html', 
                         patients=patients,
                         doctors=doctors,
                         today_appointments=today_appointments,
                         today_appointments_count=today_appointments_count,
                         total_pending_count=total_pending_count,
                         admitted_count=admitted_count,
                         specializations=all_specializations,
                         now=now)

@app.route('/admin/delete_patient/<int:patient_id>', methods=['POST'])
@login_required
def delete_patient(patient_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    patient = Patient.query.get_or_404(patient_id)
    if patient.is_admin:
        return jsonify({'error': 'Cannot delete admin user'}), 400
    
    db.session.delete(patient)
    db.session.commit()
    return jsonify({'message': 'Patient deleted successfully'})

@app.route('/admin/update_appointment_status/<int:appointment_id>', methods=['POST'])
@login_required
def update_appointment_status(appointment_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    appointment = Appointment.query.get_or_404(appointment_id)
    status = request.form.get('status')
    
    if status not in ['pending', 'completed', 'cancelled']:
        return jsonify({'error': 'Invalid status'}), 400
    
    # If the appointment is being cancelled, free up the slot
    if status == 'cancelled' and appointment.status != 'cancelled':
        slot = appointment.date_specific_slot
        if slot:
            slot.appointments_count = max(0, slot.appointments_count - 1)
            # If the slot was full and now has an opening, mark it as available again
            if not slot.is_available and slot.appointments_count < 10:
                slot.is_available = True
    
    appointment.status = status
    db.session.commit()
    return jsonify({'message': 'Appointment status updated successfully'})

@app.route('/admin/delete_doctor/<int:doctor_id>', methods=['POST'])
@login_required
def delete_doctor(doctor_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    doctor = Doctor.query.get_or_404(doctor_id)
    db.session.delete(doctor)
    db.session.commit()
    return jsonify({'message': 'Doctor deleted successfully'})

@app.route('/admin/edit_doctor/<int:doctor_id>', methods=['GET', 'POST'])
@login_required
def edit_doctor(doctor_id):
    if not current_user.is_admin:
        return redirect(url_for('dashboard'))
    
    doctor = Doctor.query.get_or_404(doctor_id)
    
    if request.method == 'POST':
        doctor.name = request.form.get('name')
        doctor.specialization = request.form.get('specialization')
        db.session.commit()
        flash('Doctor information updated successfully', 'success')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('edit_doctor.html', doctor=doctor)

@app.route('/admin/manage_slots/<int:doctor_id>', methods=['GET', 'POST'])
@login_required
def manage_slots(doctor_id):
    if not current_user.is_admin:
        return redirect(url_for('dashboard'))
    
    doctor = Doctor.query.get_or_404(doctor_id)
    
    if request.method == 'POST':
        # Clear existing slots
        DateSpecificSlot.query.filter_by(doctor_id=doctor_id).delete()
        
        # Add new slots
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        for day in range(5):
            start_time = request.form.get(f'start_time_{day}')
            end_time = request.form.get(f'end_time_{day}')
            is_available = request.form.get(f'is_available_{day}') == 'on'
            
            if start_time and end_time:
                slot = DateSpecificSlot(
                    doctor_id=doctor_id,
                    date=datetime.now().date(),
                    start_time=start_time,
                    end_time=end_time,
                    is_available=is_available
                )
                db.session.add(slot)
        
        db.session.commit()
        flash('Doctor slots updated successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('manage_slots.html', doctor=doctor)

@app.route('/admin/manage_date_slots/<int:doctor_id>', methods=['GET', 'POST'])
@login_required
def manage_date_slots(doctor_id):
    if not current_user.is_admin:
        return redirect(url_for('dashboard'))
    
    doctor = Doctor.query.get_or_404(doctor_id)
    date_str = request.args.get('date')
    
    if date_str:
        try:
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid date format', 'danger')
            selected_date = datetime.now().date()
    else:
        selected_date = datetime.now().date()
    
    if request.method == 'POST':
        try:
            # Get the date from form data
            selected_date = datetime.strptime(request.form.get('selected_date'), '%Y-%m-%d').date()
            
            # Delete existing slots for this date and doctor that don't have appointments
            existing_slots = DateSpecificSlot.query.filter_by(
                doctor_id=doctor_id, 
                date=selected_date
            ).all()
            
            # Only delete slots that don't have appointments
            for slot in existing_slots:
                if not slot.appointments:
                    db.session.delete(slot)
                    
            db.session.commit()
            
            # Get all start and end times from the form
            start_times = request.form.getlist('start_time[]')
            end_times = request.form.getlist('end_time[]')
            
            # Process each time range
            for start_time, end_time in zip(start_times, end_times):
                if start_time and end_time:
                    # Convert times to datetime objects for time calculations
                    start_dt = datetime.strptime(start_time, '%H:%M')
                    end_dt = datetime.strptime(end_time, '%H:%M')
                    
                    # Create 1-hour slots within the range
                    current_time = start_dt
                    while current_time < end_dt:
                        # Calculate the end time for this 1-hour slot
                        next_time = current_time + timedelta(hours=1)
                        
                        # If next_time exceeds the end_dt, cap it at end_dt
                        if next_time > end_dt:
                            next_time = end_dt
                        
                        # Format times as strings
                        current_time_str = current_time.strftime('%H:%M')
                        next_time_str = next_time.strftime('%H:%M')
                        
                        # Check if this 1-hour slot already exists
                        existing_slot = DateSpecificSlot.query.filter_by(
                            doctor_id=doctor_id,
                            date=selected_date,
                            start_time=current_time_str,
                            end_time=next_time_str
                        ).first()
                        
                        if existing_slot:
                            # Ensure it's marked as available
                            existing_slot.is_available = True
                            # If we want to reset appointments_count, uncomment below
                            # existing_slot.appointments_count = 0
                        else:
                            # Create new 1-hour slot
                            new_slot = DateSpecificSlot(
                                doctor_id=doctor_id,
                                date=selected_date,
                                start_time=current_time_str,
                                end_time=next_time_str,
                                is_available=True,
                                appointments_count=0
                            )
                            db.session.add(new_slot)
                        
                        # Move to the next hour
                        current_time = next_time
            
            db.session.commit()
            flash(f'Slots for {selected_date.strftime("%B %d, %Y")} have been updated successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating slots: {str(e)}', 'danger')
        
        return redirect(url_for('manage_date_slots', doctor_id=doctor_id, date=selected_date.strftime('%Y-%m-%d')))
    
    # Get all slots for the selected date
    slots = DateSpecificSlot.query.filter_by(
        doctor_id=doctor_id, 
        date=selected_date
    ).order_by(DateSpecificSlot.start_time).all()
    
    # Get all dates with slots for this doctor
    dates_with_slots = db.session.query(DateSpecificSlot.date)\
                       .filter_by(doctor_id=doctor_id)\
                       .distinct()\
                       .order_by(DateSpecificSlot.date).all()
    
    dates_with_slots = [date[0] for date in dates_with_slots]
    
    return render_template('manage_date_slots.html', 
                         doctor=doctor, 
                         slots=slots, 
                         selected_date=selected_date,
                         dates_with_slots=dates_with_slots,
                         timedelta=timedelta)

@app.route('/book_appointment', methods=['POST'])
@login_required
def book_appointment():
    doctor_id = request.form.get('doctor_id')
    appointment_date = datetime.strptime(request.form.get('date'), '%Y-%m-%d').date()
    appointment_time = request.form.get('time')
    patient_name = request.form.get('patient_name')
    patient_age = request.form.get('patient_age')
    patient_gender = request.form.get('patient_gender')
    department = request.form.get('department')
    
    # Validate required fields
    if not all([doctor_id, appointment_date, appointment_time, patient_name, patient_age, patient_gender, department]):
        flash('All fields are required', 'danger')
        return redirect(url_for('dashboard'))
    
    # Validate age
    try:
        patient_age = int(patient_age)
        if patient_age < 1 or patient_age > 120:
            flash('Please enter a valid age (1-120)', 'danger')
            return redirect(url_for('dashboard'))
    except ValueError:
        flash('Please enter a valid age', 'danger')
        return redirect(url_for('dashboard'))
    
    # Check if slot exists and is available
    slot = DateSpecificSlot.query.filter_by(
        doctor_id=doctor_id,
        date=appointment_date,
        start_time=appointment_time,
        is_available=True
    ).first()
    
    if not slot:
        flash('Selected time slot is not available', 'danger')
        return redirect(url_for('dashboard'))
    
    # Check if the slot has reached its maximum capacity (10 appointments)
    if slot.appointments_count >= 10:
        flash('This time slot is already fully booked. Please select another time.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Create the appointment
    appointment = Appointment(
        patient_id=current_user.id,
        doctor_id=doctor_id,
        date_specific_slot_id=slot.id,
        date=appointment_date,
        time=appointment_time,
        patient_name=patient_name,
        patient_age=patient_age,
        patient_gender=patient_gender,
        department=department,
        patient_email=current_user.email
    )
    
    # Update slot availability
    slot.appointments_count += 1
    if slot.appointments_count >= 10:  # Maximum capacity reached
        slot.is_available = False
    
    db.session.add(appointment)
    db.session.commit()
    
    flash('Appointment booked successfully!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/cancel_appointment/<int:appointment_id>')
@login_required
def cancel_appointment(appointment_id):
    try:
        appointment = Appointment.query.get_or_404(appointment_id)
        if appointment.patient_id == current_user.id or current_user.is_admin:
            # Instead of deleting, mark as cancelled
            appointment.status = 'cancelled'
            
            # Free up the slot
            slot = appointment.date_specific_slot
            if slot:
                print(f"Before update: Slot ID {slot.id}, appointments_count: {slot.appointments_count}, is_available: {slot.is_available}")
                slot.appointments_count = max(0, slot.appointments_count - 1)
                # If the slot was full and now has an opening, mark it as available again
                if not slot.is_available and slot.appointments_count < 10:
                    slot.is_available = True
                print(f"After update: Slot ID {slot.id}, appointments_count: {slot.appointments_count}, is_available: {slot.is_available}")
            else:
                print(f"Warning: No slot found for appointment {appointment_id}")
            
            db.session.commit()
            flash('Appointment cancelled successfully!')
        else:
            flash('You do not have permission to cancel this appointment.', 'danger')
    except Exception as e:
        db.session.rollback()
        print(f"Error cancelling appointment {appointment_id}: {str(e)}")
        flash(f'Error cancelling appointment: {str(e)}', 'danger')
    
    return redirect(url_for('dashboard'))

@app.route('/admin/add_doctor', methods=['GET', 'POST'])
@login_required
def add_doctor():
    if not current_user.is_admin:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        specialization = request.form.get('specialization')
        qualifications = request.form.get('qualifications')
        years_of_experience = int(request.form.get('years_of_experience', 15))
        
        doctor = Doctor(
            name=name,
            specialization=specialization,
            qualifications=qualifications,
            years_of_experience=years_of_experience
        )
        db.session.add(doctor)
        db.session.commit()
        
        flash('Doctor added successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('add_doctor.html')

@app.route('/get_available_slots/<int:doctor_id>/<string:date_str>')
def get_available_slots(doctor_id, date_str):
    try:
        # Convert date string to date object
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # Get all slots for the doctor on the selected date
        slots = DateSpecificSlot.query.filter_by(
            doctor_id=doctor_id,
            date=selected_date
        ).all()
        
        # Format the results
        slots_data = []
        for slot in slots:
            slots_data.append({
                'id': slot.id,
                'start_time': slot.start_time,
                'end_time': slot.end_time,
                'available': slot.is_available and slot.appointments_count < 10
            })
        
        return jsonify(slots_data)
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/admin/register_patient', methods=['GET', 'POST'])
@login_required
def admin_register_patient():
    if not current_user.is_admin:
        flash('Access denied')
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        phone_number = request.form['phone_number']
        
        if Patient.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('admin_register_patient'))
            
        if Patient.query.filter_by(email=email).first():
            flash('Email already registered')
            return redirect(url_for('admin_register_patient'))
            
        patient = Patient(username=username, email=email, phone_number=phone_number)
        patient.set_password(password)
        db.session.add(patient)
        db.session.commit()
        
        flash('Patient registered successfully!')
        return redirect(url_for('admin_dashboard'))
        
    return render_template('admin_register_patient.html')

@app.route('/admin/book_appointment', methods=['GET', 'POST'])
@login_required
def admin_book_appointment():
    if not current_user.is_admin:
        flash('Access denied')
        return redirect(url_for('dashboard'))
    
    # Get unique specializations for the dropdown
    all_specializations = [doc.specialization for doc in Doctor.query.with_entities(Doctor.specialization).distinct()]
    now = datetime.now()
    
    if request.method == 'POST':
        patient_name = request.form.get('patient_name')
        patient_age = request.form.get('patient_age')
        patient_phone = request.form.get('patient_phone')
        patient_gender = request.form.get('patient_gender')
        patient_email = request.form.get('patient_email', '')  # Get email if provided, default to empty string
        department = request.form.get('department')
        doctor_id = request.form.get('doctor_id')
        appointment_date = datetime.strptime(request.form.get('date'), '%Y-%m-%d').date()
        appointment_time = request.form.get('time')
        
        # Validation
        if not all([patient_name, patient_age, patient_phone, patient_gender, department, doctor_id, appointment_date, appointment_time]):
            flash('All fields are required')
            return redirect(url_for('admin_book_appointment'))
        
        # Validate Indian phone number - 10 digits
        if not (patient_phone.isdigit() and len(patient_phone) == 10):
            flash('Please enter a valid 10-digit Indian phone number')
            return redirect(url_for('admin_book_appointment'))
        
        # Check if slot exists and is available
        slot = DateSpecificSlot.query.filter_by(
            doctor_id=doctor_id,
            date=appointment_date,
            start_time=appointment_time,
            is_available=True
        ).first()
        
        if not slot:
            flash('Selected time slot is not available')
            return redirect(url_for('admin_book_appointment'))
        
        # Check if the slot has reached its maximum capacity (10 appointments)
        if slot.appointments_count >= 10:
            flash('This time slot is already fully booked (10 appointments). Please select another time.', 'danger')
            return redirect(url_for('admin_book_appointment'))
        
        # Check if patient exists, if not create a temporary one
        patient = Patient.query.filter_by(phone_number=patient_phone, is_admin=False).first()
        
        if not patient:
            # Create a temporary patient 
            username = f"patient_{patient_phone}"
            email = patient_email or f"{username}@placeholder.com"  # Use provided email if available
            temp_password = f"temp{patient_phone[-4:]}"
            
            # Check if username exists
            if Patient.query.filter_by(username=username).first():
                # Add a timestamp to make it unique
                username = f"{username}_{int(datetime.now().timestamp())}"
            
            patient = Patient(
                username=username,
                email=email,
                phone_number=patient_phone,
                is_admin=False
            )
            patient.set_password(temp_password)
            db.session.add(patient)
            db.session.commit()
        
        # Create the appointment
        appointment = Appointment(
            patient_id=patient.id,
            doctor_id=doctor_id,
            date_specific_slot_id=slot.id,
            date=appointment_date,
            time=appointment_time,
            registered_by_admin=True,
            patient_name=patient_name,
            patient_email=patient_email or patient.email,  # Use provided email or patient's email
            patient_age=patient_age,
            patient_gender=patient_gender,
            department=department
        )
        
        # Update slot availability
        slot.appointments_count += 1
        if slot.appointments_count >= 10:  # Maximum capacity reached (10 appointments)
            slot.is_available = False
            
        db.session.add(appointment)
        db.session.commit()
        
        flash('Appointment booked successfully!')
        return redirect(url_for('admin_dashboard'))
    
    # GET request - show the form
    return render_template('admin_book_appointment.html', specializations=all_specializations, now=now, doctors=[])

@app.route('/get_doctors_by_department/<department>')
@login_required
def get_doctors_by_department(department):
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    doctors = Doctor.query.filter_by(specialization=department).all()
    return jsonify([{
        'id': doctor.id,
        'name': doctor.name,
        'experience': doctor.years_of_experience
    } for doctor in doctors])

@app.route('/admin/view_all_patients')
@login_required
def view_all_patients():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get search parameters
    patient_name = request.args.get('patient_name', '')
    doctor_name = request.args.get('doctor_name', '')
    department = request.args.get('department', '')
    date_str = request.args.get('date', '')
    
    # First query: Get patients with completed appointments
    completed_appointments_query = Appointment.query.filter_by(status='completed')
    
    # Apply filters to completed appointments
    if patient_name:
        completed_appointments_query = completed_appointments_query.filter(
            db.or_(
                Appointment.patient_name.ilike(f'%{patient_name}%'),
                Appointment.patient.has(Patient.username.ilike(f'%{patient_name}%'))
            )
        )
    
    if doctor_name:
        completed_appointments_query = completed_appointments_query.filter(
            Appointment.doctor.has(Doctor.name.ilike(f'%{doctor_name}%'))
        )
    
    if department:
        completed_appointments_query = completed_appointments_query.filter(
            db.or_(
                Appointment.department == department,
                Appointment.doctor.has(Doctor.specialization == department)
            )
        )
    
    # Filter by date if provided
    if date_str:
        try:
            filter_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            completed_appointments_query = completed_appointments_query.filter(Appointment.date == filter_date)
        except ValueError:
            flash('Invalid date format', 'warning')
    
    # Get all filtered completed appointments
    completed_appointments = completed_appointments_query.all()
    
    # Organize data by patient
    patients_with_history = {}
    
    # Add all patients with completed appointments
    for appointment in completed_appointments:
        patient_id = appointment.patient_id
        if patient_id not in patients_with_history:
            patient = Patient.query.get(patient_id)
            if patient:
                # Initialize with actual patient data
                patient.completed_appointments = []
                patient.display_name = appointment.patient_name or patient.username
                
                # Use patient_email from appointment if it exists
                if appointment.patient_email:
                    patient.email = appointment.patient_email
                
                patients_with_history[patient_id] = patient
        
        if patient_id in patients_with_history:
            patients_with_history[patient_id].completed_appointments.append(appointment)
    
    # Convert dictionary to list for template
    patients_list = list(patients_with_history.values())
    
    # Get unique specializations for the dropdown
    all_specializations = [doc.specialization for doc in Doctor.query.with_entities(Doctor.specialization).distinct()]
    
    return render_template('view_all_patients.html',
                          patients=patients_list,
                          specializations=all_specializations)

@app.route('/admin/view_all_pending')
@login_required
def view_all_pending():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get search parameters
    patient_name = request.args.get('patient_name', '')
    doctor_name = request.args.get('doctor_name', '')
    department = request.args.get('department', '')
    date_str = request.args.get('date', '')
    
    # Base query for all non-completed appointments
    appointments_query = Appointment.query.filter(Appointment.status != 'completed')
    
    # Apply filters if provided
    if patient_name:
        # Search by patient_name field or by username
        appointments_query = appointments_query.filter(
            db.or_(
                Appointment.patient_name.ilike(f'%{patient_name}%'),
                Appointment.patient.has(Patient.username.ilike(f'%{patient_name}%'))
            )
        )
    
    if doctor_name:
        # Search by doctor name
        appointments_query = appointments_query.filter(
            Appointment.doctor.has(Doctor.name.ilike(f'%{doctor_name}%'))
        )
    
    if department:
        # Search by department field or by doctor's specialization
        appointments_query = appointments_query.filter(
            db.or_(
                Appointment.department == department,
                Appointment.doctor.has(Doctor.specialization == department)
            )
        )
    
    # Filter by date if provided
    if date_str:
        try:
            filter_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            appointments_query = appointments_query.filter(Appointment.date == filter_date)
        except ValueError:
            flash('Invalid date format', 'warning')
    
    # Get appointments with filters applied, ordered by date and time
    pending_appointments = appointments_query.order_by(Appointment.date, Appointment.time).all()
    
    # Get unique specializations for the dropdown
    all_specializations = [doc.specialization for doc in Doctor.query.with_entities(Doctor.specialization).distinct()]
    
    # Get current date for the date input min attribute
    now = datetime.now()
    
    return render_template('view_all_pending.html',
                          pending_appointments=pending_appointments,
                          specializations=all_specializations,
                          now=now)

@app.route('/admin/doctors')
@login_required
def view_all_doctors():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get search parameters
    doctor_name = request.args.get('name', '')
    specialization = request.args.get('specialization', '')
    
    # Base query for doctors
    doctors_query = Doctor.query
    
    # Apply filters if provided
    if doctor_name:
        doctors_query = doctors_query.filter(Doctor.name.ilike(f'%{doctor_name}%'))
    
    if specialization:
        doctors_query = doctors_query.filter(Doctor.specialization == specialization)
    
    # Get doctors with filters applied
    doctors = doctors_query.all()
    
    # Get unique specializations for the dropdown
    all_specializations = [doc.specialization for doc in Doctor.query.with_entities(Doctor.specialization).distinct()]
    
    return render_template('view_all_doctors.html',
                          doctors=doctors,
                          specializations=all_specializations)

@app.route('/admin/admitted_patients')
@login_required
def view_admitted_patients():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get search parameters
    patient_name = request.args.get('patient_name', '')
    doctor_name = request.args.get('doctor_name', '')
    status = request.args.get('status', '')
    date_str = request.args.get('date', '')
    
    # Base query for admitted patients
    patients_query = AdmittedPatient.query
    
    # Apply filters if provided
    if patient_name:
        patients_query = patients_query.filter(AdmittedPatient.patient_name.ilike(f'%{patient_name}%'))
    
    if doctor_name:
        patients_query = patients_query.filter(AdmittedPatient.doctor.has(Doctor.name.ilike(f'%{doctor_name}%')))
    
    if status:
        patients_query = patients_query.filter(AdmittedPatient.status == status)
    
    # Filter by admission date if provided
    if date_str:
        try:
            filter_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            patients_query = patients_query.filter(AdmittedPatient.admission_date == filter_date)
        except ValueError:
            flash('Invalid date format', 'warning')
    
    # Get all admitted patients with filters applied
    admitted_patients = patients_query.order_by(AdmittedPatient.admission_date.desc()).all()
    
    # Get all doctors for the dropdown
    doctors = Doctor.query.all()
    
    # Define room numbers and their capacities
    ROOM_CAPACITIES = {
        '101': 25,
        '102': 25,
        '103': 25,
        '104': 25,
        '201': 25,
        '202': 25,
        '203': 25,
        '204': 25,
        'ICU': 5,
        'Operation Theatre': 5
    }
    
    # Get current room occupancy
    room_counts = {}
    for room_number in ROOM_CAPACITIES.keys():
        count = AdmittedPatient.query.filter_by(room_number=room_number, status='admitted').count()
        room_counts[room_number] = count
    
    # Get current date for the discharge modal
    now = datetime.now()
    
    return render_template('admitted_patients.html',
                          admitted_patients=admitted_patients,
                          doctors=doctors,
                          room_capacities=ROOM_CAPACITIES,
                          room_counts=room_counts,
                          now=now)

@app.route('/admin/admit_patient', methods=['GET', 'POST'])
@login_required
def admit_patient():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get all doctors for the form
    doctors = Doctor.query.all()
    
    # Define room numbers and their capacities
    ROOM_CAPACITIES = {
        '101': 25,
        '102': 25,
        '103': 25,
        '104': 25,
        '201': 25,
        '202': 25,
        '203': 25,
        '204': 25,
        'ICU': 5,
        'Operation Theatre': 5
    }
    
    # Get current room occupancy
    room_counts = {}
    for room_number in ROOM_CAPACITIES.keys():
        count = AdmittedPatient.query.filter_by(room_number=room_number, status='admitted').count()
        room_counts[room_number] = count
    
    if request.method == 'POST':
        patient_name = request.form.get('patient_name')
        patient_age = request.form.get('patient_age')
        patient_gender = request.form.get('patient_gender')
        patient_phone = request.form.get('patient_phone')
        room_number = request.form.get('room_number')
        doctor_id = request.form.get('doctor_id')
        admission_date = request.form.get('admission_date')
        diagnosis = request.form.get('diagnosis')
        notes = request.form.get('notes')
        
        # Validation
        if not all([patient_name, patient_age, patient_gender, room_number, doctor_id, admission_date]):
            flash('All required fields must be filled', 'danger')
            return redirect(url_for('admit_patient'))
        
        # Check if doctor exists
        doctor = Doctor.query.get(doctor_id)
        if not doctor:
            flash('Selected doctor does not exist', 'danger')
            return redirect(url_for('admit_patient'))
        
        # Check room capacity
        if room_number in ROOM_CAPACITIES:
            current_occupancy = AdmittedPatient.query.filter_by(
                room_number=room_number, 
                status='admitted'
            ).count()
            
            if current_occupancy >= ROOM_CAPACITIES[room_number]:
                flash(f'Room {room_number} is at full capacity ({current_occupancy}/{ROOM_CAPACITIES[room_number]}). Please select another room.', 'danger')
                return redirect(url_for('admit_patient'))
        
        # Parse admission date
        try:
            admission_date = datetime.strptime(admission_date, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid admission date format', 'danger')
            return redirect(url_for('admit_patient'))
        
        # Check if patient exists, if not create a temporary one
        patient = None
        if patient_phone:
            patient = Patient.query.filter_by(phone_number=patient_phone, is_admin=False).first()
            
            if not patient:
                # Create a temporary patient 
                username = f"patient_{patient_phone}"
                email = f"{username}@placeholder.com"
                temp_password = f"temp{patient_phone[-4:]}"
                
                # Check if username exists
                if Patient.query.filter_by(username=username).first():
                    # Add a timestamp to make it unique
                    username = f"{username}_{int(datetime.now().timestamp())}"
                
                patient = Patient(
                    username=username,
                    email=email,
                    phone_number=patient_phone,
                    is_admin=False
                )
                patient.set_password(temp_password)
                db.session.add(patient)
                db.session.commit()
        
        # Create the admission record
        admitted_patient = AdmittedPatient(
            patient_id=patient.id if patient else None,
            patient_name=patient_name,
            patient_age=int(patient_age),
            patient_gender=patient_gender,
            room_number=room_number,
            doctor_id=doctor_id,
            admission_date=admission_date,
            phone_number=patient_phone,
            diagnosis=diagnosis,
            notes=notes,
            status='admitted'
        )
        
        db.session.add(admitted_patient)
        db.session.commit()
        
        flash('Patient admitted successfully!', 'success')
        return redirect(url_for('view_admitted_patients'))
    
    # GET request - show the form
    return render_template('admit_patient.html', 
                          doctors=doctors, 
                          today=datetime.now().date(),
                          room_capacities=ROOM_CAPACITIES,
                          room_counts=room_counts)

@app.route('/admin/discharge_patient/<int:admission_id>', methods=['POST'])
@login_required
def discharge_patient(admission_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    admitted_patient = AdmittedPatient.query.get_or_404(admission_id)
    discharge_date = request.form.get('discharge_date')
    
    try:
        discharge_date = datetime.strptime(discharge_date, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        # If no date provided or invalid format, use today
        discharge_date = datetime.now().date()
    
    # Update admission record
    admitted_patient.discharge_date = discharge_date
    admitted_patient.status = 'discharged'
    
    # Save the changes
    db.session.commit()
    
    return jsonify({'message': 'Patient discharged successfully'})

@app.route('/admin/update_admission/<int:admission_id>', methods=['GET', 'POST'])
@login_required
def update_admission(admission_id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard'))
    
    admitted_patient = AdmittedPatient.query.get_or_404(admission_id)
    doctors = Doctor.query.all()
    
    # Define room numbers and their capacities
    ROOM_CAPACITIES = {
        '101': 25,
        '102': 25,
        '103': 25,
        '104': 25,
        '201': 25,
        '202': 25,
        '203': 25,
        '204': 25,
        'ICU': 5,
        'Operation Theatre': 5
    }
    
    # Get current room occupancy
    room_counts = {}
    for room_number in ROOM_CAPACITIES.keys():
        count = AdmittedPatient.query.filter_by(room_number=room_number, status='admitted').count()
        # Don't count the current patient if they're in this room
        if room_number == admitted_patient.room_number and admitted_patient.status == 'admitted':
            count = max(0, count - 1)
        room_counts[room_number] = count
    
    if request.method == 'POST':
        new_room_number = request.form.get('room_number')
        
        # Check room capacity if changing rooms and not being discharged
        if (new_room_number != admitted_patient.room_number and 
            new_room_number in ROOM_CAPACITIES and 
            not request.form.get('discharge_date')):
            
            current_occupancy = AdmittedPatient.query.filter_by(
                room_number=new_room_number, 
                status='admitted'
            ).count()
            
            if current_occupancy >= ROOM_CAPACITIES[new_room_number]:
                flash(f'Room {new_room_number} is at full capacity ({current_occupancy}/{ROOM_CAPACITIES[new_room_number]}). Please select another room.', 'danger')
                return redirect(url_for('update_admission', admission_id=admission_id))
        
        # Update patient information
        admitted_patient.patient_name = request.form.get('patient_name')
        admitted_patient.patient_age = request.form.get('patient_age')
        admitted_patient.patient_gender = request.form.get('patient_gender')
        admitted_patient.phone_number = request.form.get('patient_phone')
        admitted_patient.room_number = new_room_number
        admitted_patient.doctor_id = request.form.get('doctor_id')
        admitted_patient.diagnosis = request.form.get('diagnosis')
        admitted_patient.notes = request.form.get('notes')
        
        # Parse admission date
        try:
            admitted_patient.admission_date = datetime.strptime(
                request.form.get('admission_date'), '%Y-%m-%d'
            ).date()
        except ValueError:
            flash('Invalid admission date format', 'danger')
            return redirect(url_for('update_admission', admission_id=admission_id))
        
        # Parse discharge date if provided
        discharge_date = request.form.get('discharge_date')
        if discharge_date:
            try:
                admitted_patient.discharge_date = datetime.strptime(discharge_date, '%Y-%m-%d').date()
                admitted_patient.status = 'discharged'
            except ValueError:
                flash('Invalid discharge date format', 'danger')
                return redirect(url_for('update_admission', admission_id=admission_id))
        
        db.session.commit()
        flash('Admission information updated successfully', 'success')
        return redirect(url_for('view_admitted_patients'))
    
    # GET request - show the form
    return render_template('update_admission.html', 
                          admitted_patient=admitted_patient, 
                          doctors=doctors,
                          room_capacities=ROOM_CAPACITIES,
                          room_counts=room_counts)

@app.route('/admin/edit_patient/<int:patient_id>', methods=['GET', 'POST'])
@login_required
def edit_patient(patient_id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard'))
    
    patient = Patient.query.get_or_404(patient_id)
    
    if request.method == 'POST':
        # Update patient information
        patient.username = request.form.get('username')
        patient.email = request.form.get('email')
        patient.phone_number = request.form.get('phone_number')
        
        # Update password if provided
        new_password = request.form.get('new_password')
        if new_password and new_password.strip():
            patient.set_password(new_password)
        
        # Update appointment data if it exists
        appointments = Appointment.query.filter_by(patient_id=patient_id, status='completed').all()
        for appointment in appointments:
            # Update consistent information across all appointments
            appointment.patient_name = request.form.get('display_name')
            appointment.patient_email = request.form.get('email')
        
        db.session.commit()
        flash('Patient information updated successfully', 'success')
        return redirect(url_for('view_all_patients'))
    
    # For GET request, render the edit form
    # If patient has a display name from appointments, show it
    appointments = Appointment.query.filter_by(patient_id=patient_id, status='completed').all()
    display_name = None
    if appointments:
        display_name = appointments[0].patient_name
    
    return render_template('edit_patient.html', patient=patient, display_name=display_name)

@app.route('/admin/view_cancelled_appointments')
@login_required
def view_cancelled_appointments():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get search parameters
    patient_name = request.args.get('patient_name', '')
    doctor_name = request.args.get('doctor_name', '')
    department = request.args.get('department', '')
    date_str = request.args.get('date', '')
    
    # Base query for cancelled appointments
    appointments_query = Appointment.query.filter_by(status='cancelled')
    
    # Apply filters if provided
    if patient_name:
        # Search by patient_name field or by username
        appointments_query = appointments_query.filter(
            db.or_(
                Appointment.patient_name.ilike(f'%{patient_name}%'),
                Appointment.patient.has(Patient.username.ilike(f'%{patient_name}%'))
            )
        )
    
    if doctor_name:
        # Search by doctor name
        appointments_query = appointments_query.filter(
            Appointment.doctor.has(Doctor.name.ilike(f'%{doctor_name}%'))
        )
    
    if department:
        # Search by department field or by doctor's specialization
        appointments_query = appointments_query.filter(
            db.or_(
                Appointment.department == department,
                Appointment.doctor.has(Doctor.specialization == department)
            )
        )
    
    # Filter by date if provided
    if date_str:
        try:
            filter_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            appointments_query = appointments_query.filter(Appointment.date == filter_date)
        except ValueError:
            flash('Invalid date format', 'warning')
    
    # Get cancelled appointments with filters applied, ordered by date
    cancelled_appointments = appointments_query.order_by(Appointment.date.desc()).all()
    
    # Get unique specializations for the dropdown
    all_specializations = [doc.specialization for doc in Doctor.query.with_entities(Doctor.specialization).distinct()]
    
    # Get current date for the reschedule modal min date
    now = datetime.now()
    
    return render_template('admin/view_cancelled_appointments.html',
                          cancelled_appointments=cancelled_appointments,
                          specializations=all_specializations,
                          now=now)

@app.route('/admin/reschedule_appointment/<int:appointment_id>', methods=['POST'])
@login_required
def reschedule_appointment(appointment_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    appointment = Appointment.query.get_or_404(appointment_id)
    
    # Only cancelled appointments can be rescheduled
    if appointment.status != 'cancelled':
        return jsonify({'error': 'Only cancelled appointments can be rescheduled'}), 400
    
    # Get the new date and time from the form
    doctor_id = request.form.get('doctor_id')
    new_date_str = request.form.get('new_date')
    new_time = request.form.get('new_time')
    
    if not all([doctor_id, new_date_str, new_time]):
        return jsonify({'error': 'Missing required fields'}), 400
    
    try:
        new_date = datetime.strptime(new_date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400
    
    # Check if the selected slot exists and is available
    slot = DateSpecificSlot.query.filter_by(
        doctor_id=doctor_id,
        date=new_date,
        start_time=new_time,
        is_available=True
    ).first()
    
    if not slot:
        return jsonify({'error': 'Selected time slot is not available'}), 400
    
    # Check if the slot has reached its maximum capacity
    if slot.appointments_count >= 10:
        return jsonify({'error': 'This time slot is already fully booked. Please select another time.'}), 400
    
    # Update the appointment with the new date, time, and slot
    appointment.date = new_date
    appointment.time = new_time
    appointment.date_specific_slot_id = slot.id
    appointment.status = 'pending'  # Set status back to pending
    
    # Update slot availability
    slot.appointments_count += 1
    if slot.appointments_count >= 10:  # Maximum capacity reached
        slot.is_available = False
    
    db.session.commit()
    
    return jsonify({'message': 'Appointment rescheduled successfully!'})

@app.route('/health')
def health_check():
    """Health check endpoint to verify the app is running."""
    return jsonify({
        'status': 'healthy',
        'version': '1.0.0',
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    app.run() 