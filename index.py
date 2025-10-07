from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///lab_system.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Models
class Analyte(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer)
    gender = db.Column(db.String(10))
    registered_at = db.Column(db.DateTime, default=datetime.utcnow)
    tests = db.relationship('PatientTest', backref='patient', lazy=True, cascade='all, delete-orphan')

class PatientTest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    analyte_id = db.Column(db.Integer, db.ForeignKey('analyte.id'), nullable=False)
    result = db.Column(db.String(50), nullable=True)  # e.g., numerical value or 'pending'
    result_date = db.Column(db.DateTime, default=datetime.utcnow)
    analyte = db.relationship('Analyte', backref='patient_tests')

# Create tables
with app.app_context():
    db.create_all()

# Routes

# Page 1: Register Patient
@app.route('/', methods=['GET', 'POST'])
def register_patient():
    analytes = Analyte.query.all()
    if request.method == 'POST':
        name = request.form['name']
        age = request.form.get('age', type=int)
        gender = request.form['gender']
        
        patient = Patient(name=name, age=age, gender=gender)
        db.session.add(patient)
        db.session.flush()  # To get patient.id
        
        # Add selected tests
        selected_analytes = request.form.getlist('analytes')
        for analyte_id in selected_analytes:
            test = PatientTest(patient_id=patient.id, analyte_id=int(analyte_id))
            db.session.add(test)
        
        db.session.commit()
        flash('Patient registered successfully!')
        return redirect(url_for('list_patients'))
    
    return render_template('register.html', analytes=analytes)

# Page 2: List Patients
@app.route('/patients')
def list_patients():
    patients = Patient.query.all()
    return render_template('patients.html', patients=patients)

# Edit Patient Lab Results
@app.route('/patient/<int:patient_id>/edit', methods=['GET', 'POST'])
def edit_patient(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    if request.method == 'POST':
        for test_id, result in request.form.items():
            if test_id.startswith('result_'):
                test = PatientTest.query.get(int(test_id.split('_')[1]))
                if test:
                    test.result = result
                    test.result_date = datetime.utcnow()
        db.session.commit()
        flash('Lab results updated successfully!')
        return redirect(url_for('list_patients'))
    
    return render_template('edit_patient.html', patient=patient)

# Page 3: Create New Analyte
@app.route('/analytes/new', methods=['GET', 'POST'])
def create_analyte():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form.get('description')
        
        analyte = Analyte(name=name, description=description)
        db.session.add(analyte)
        db.session.commit()
        flash('Analyte created successfully!')
        return redirect(url_for('register_patient'))  # Redirect back to registration
    
    return render_template('create_analyte.html')

if __name__ == '__main__':
    app.run(debug=True)
