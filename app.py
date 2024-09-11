from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_mail import Mail, Message
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from db import db
from models import Student, CEO

# Initialize extensions
jwt = JWTManager()
mail = Mail()

def create_app():
    app = Flask(__name__)

    # App configuration
    app.config['SECRET_KEY'] = 'your_secret_key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///job.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = 'your_jwt_secret'

    # Mail configuration
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = 'marierareagan@gmail.com'
    app.config['MAIL_PASSWORD'] = 'ppwkysfmuntbeayn'
    app.config['MAIL_DEFAULT_SENDER'] = 'marierareagan@gmail.com'

    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    mail.init_app(app)
    CORS(app)

    # Create tables
    with app.app_context():
        db.create_all()

    # Register route
    @app.route('/register', methods=['POST'])
    def register():
        data = request.json
        role = data.get('role')
        name = data.get('name')
        email = data.get('email')
        password = data.get('password')

        if role not in ['student', 'ceo']:
            return jsonify({'message': 'Invalid role.'}), 400
        
        if role == 'student':
            if Student.query.filter_by(email=email).first():
                return jsonify({'message': 'Student with this email already exists.'}), 400
            if Student.query.filter_by(nationality_number=data.get('nationality_number')).first():
                return jsonify({'message': 'Student with this nationality number already exists.'}), 400

            hashed_password = generate_password_hash(password)
            try:
                dob = datetime.strptime(data.get('date_of_birth'), '%Y-%m-%d')
            except ValueError:
                return jsonify({'message': 'Invalid date format. Use YYYY-MM-DD.'}), 400
            
            new_student = Student(
                name=name,
                email=email,
                password_hash=hashed_password,
                nationality_number=data.get('nationality_number'),
                branch=data.get('branch'),
                amount_paid=data.get('amount_paid', 0.0),
                top_up=data.get('top_up', 0.0),
                balance=data.get('balance', 0.0),
                status=data.get('status', 'active')
            )
            db.session.add(new_student)
            db.session.commit()

            # Send welcome email to student
            try:
                msg = Message('Welcome to the Driving School', recipients=[email])
                msg.body = f'Hi {name},\n\nWelcome to the SKYNET Driving School.'
                mail.send(msg)
            except Exception as e:
                return jsonify({'message': f'Failed to send welcome email: {str(e)}'}), 500

            # Notify CEO
            ceo_email = 'skynetdrivingschoolltd@gmail.com'
            if ceo_email:
                try:
                    msg = Message('New Student Registration', recipients=[ceo_email])
                    msg.body = f'A new student has registered.\nName: {name}\nEmail: {email}.'
                    mail.send(msg)
                except Exception as e:
                    return jsonify({'message': f'Failed to send notification email to CEO: {str(e)}'}), 500

            return jsonify({'message': 'Student registered successfully.'}), 201

        elif role == 'ceo':
            if CEO.query.filter_by(email=email).first():
                return jsonify({'message': 'CEO with this email already exists.'}), 400

            hashed_password = generate_password_hash(password)
            
            new_ceo = CEO(
                name=name,
                email=email,
                password_hash=hashed_password
            )
            db.session.add(new_ceo)
            db.session.commit()
            
            return jsonify({'message': 'CEO registered successfully.'}), 201

    # Login route
    @app.route('/login', methods=['POST'])
    def login():
        data = request.json
        email = data.get('email')
        password = data.get('password')
        
        student = Student.query.filter_by(email=email).first()
        ceo = CEO.query.filter_by(email=email).first()

        user = student or ceo
        if user and check_password_hash(user.password_hash, password):
            role = 'CEO' if ceo else 'Student'
            access_token = create_access_token(identity={'id': user.id, 'role': role})
            return jsonify({'access_token': access_token}), 200
        
        return jsonify({'message': 'Invalid credentials.'}), 401

    # Create student (CEO access only)
    @app.route('/students', methods=['POST'])
    @jwt_required()
    def create_student():
        current_user = get_jwt_identity()
        if current_user['role'] != 'CEO':
            return jsonify({'message': 'Unauthorized access.'}), 403

        data = request.json
        name = data.get('name')
        email = data.get('email')
        password = data.get('password')
        nationality_number = data.get('nationality_number')
        branch = data.get('branch')
        amount_paid = data.get('amount_paid', 0.0)
        top_up = data.get('top_up', 0.0)
        balance = data.get('balance', 0.0)
        status = data.get('status', 'active')
        
        if Student.query.filter_by(email=email).first():
            return jsonify({'message': 'Student with this email already exists.'}), 400

        if Student.query.filter_by(nationality_number=nationality_number).first():
            return jsonify({'message': 'Student with this nationality number already exists.'}), 400

        hashed_password = generate_password_hash(password)
        
        new_student = Student(
            name=name,
            email=email,
            password_hash=hashed_password,
            nationality_number=nationality_number,
            branch=branch,
            amount_paid=amount_paid,
            top_up=top_up,
            balance=balance,
            status=status
        )
        db.session.add(new_student)
        db.session.commit()
        
        return jsonify({'message': 'Student created successfully.'}), 201

    # Get current student info
    @app.route('/student', methods=['GET'])
    @jwt_required()
    def get_student():
        current_user = get_jwt_identity()
        student = Student.query.get(current_user['id'])
        
        if student:
            return jsonify({
                'id': student.id,
                'name': student.name,
                'email': student.email,
                'branch': student.branch,
                'amount_paid': student.amount_paid,
                'top_up': student.top_up,
                'balance': student.balance,
                'nationality_number': student.nationality_number,
                'status': student.status,
                'phone_number': student.phone_number,  # Add phone number
                'last_updated': student.last_updated
            }), 200
        
        return jsonify({'message': 'Student not found.'}), 404

    # Get student by ID (CEO access only)
    @app.route('/students/<int:student_id>', methods=['GET'])
    @jwt_required()
    def get_student_by_id(student_id):
        current_user = get_jwt_identity()
        if current_user['role'] != 'CEO':
            return jsonify({'message': 'Unauthorized access.'}), 403

        student = Student.query.get(student_id)
        if student:
            return jsonify({
                'id': student.id,
                'name': student.name,
                'email': student.email,
                'branch': student.branch,
                'amount_paid': student.amount_paid,
                'top_up': student.top_up,
                'balance': student.balance,
                'nationality_number': student.nationality_number,
                'status': student.status,
                'phone_number': student.phone_number,  # Add phone number
                'last_updated': student.last_updated
            }), 200
        
        return jsonify({'message': 'Student not found.'}), 404

    # Update student (CEO access only)
    @app.route('/students/<int:student_id>', methods=['PUT'])
    @jwt_required()
    def update_student(student_id):
        current_user = get_jwt_identity()
        if current_user['role'] != 'CEO':
            return jsonify({'message': 'Unauthorized access.'}), 403

        data = request.get_json()
        student = Student.query.get_or_404(student_id)

        student.name = data.get('name', student.name)
        student.email = data.get('email', student.email)
        student.branch = data.get('branch', student.branch)
        student.amount_paid = data.get('amount_paid', student.amount_paid)
        student.top_up = data.get('top_up', student.top_up)
        student.balance = data.get('balance', student.balance)
        student.status = data.get('status', student.status)
        student.phone_number = data.get('phone_number', student.phone_number)

        # Handle date fields
        student.date_amount_paid_updated = data.get('date_amount_paid_updated', student.date_amount_paid_updated)
        student.date_top_up_updated = data.get('date_top_up_updated', student.date_top_up_updated)
        student.date_balance_updated = data.get('date_balance_updated', student.date_balance_updated)

        db.session.commit()

        return jsonify({
            'id': student.id,
            'name': student.name,
            'email': student.email,
            'branch': student.branch,
            'amount_paid': student.amount_paid,
            'top_up': student.top_up,
            'balance': student.balance,
            'status': student.status,
            'phone_number': student.phone_number,
            'date_amount_paid_updated': student.date_amount_paid_updated,
            'date_top_up_updated': student.date_top_up_updated,
            'date_balance_updated': student.date_balance_updated,
            'last_updated': student.last_updated
        })

    # Delete student (CEO access only)
    @app.route('/students/<int:student_id>', methods=['DELETE'])
    @jwt_required()
    def delete_student(student_id):
        current_user = get_jwt_identity()
        if current_user['role'] != 'CEO':
            return jsonify({'message': 'Unauthorized access.'}), 403

        student = Student.query.get(student_id)
        if student:
            db.session.delete(student)
            db.session.commit()
            return jsonify({'message': 'Student deleted successfully.'}), 200
        
        return jsonify({'message': 'Student not found.'}), 404

    # Get all students (CEO access only)
    @app.route('/students', methods=['GET'])
    @jwt_required()
    def get_all_students():
        current_user = get_jwt_identity()
        if current_user['role'] != 'CEO':
            return jsonify({'message': 'Unauthorized access.'}), 403

        students = Student.query.all()
        student_list = [{
            'id': student.id,
            'name': student.name,
            'email': student.email,
            'branch': student.branch,
            'amount_paid': student.amount_paid,
            'top_up': student.top_up,
            'balance': student.balance,
            'nationality_number': student.nationality_number,
            'status': student.status,
            'phone_number': student.phone_number,  # Add phone number
            'last_updated': student.last_updated
        } for student in students]
        
        return jsonify(student_list), 200

    return app

# Initialize app
app = create_app()

if __name__ == '__main__':
    app.run(debug=True)