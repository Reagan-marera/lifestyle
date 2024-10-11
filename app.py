from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_mail import Mail, Message
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from db import db
from models import Student, CEO, Branch, BranchCEO
from flask_migrate import Migrate

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
    app.config['MAIL_USERNAME'] = 'marierareagan@gmail.com'  # Change to your email
    app.config['MAIL_PASSWORD'] = 'ppwkysfmuntbeayn'  # Change to your email password
    app.config['MAIL_DEFAULT_SENDER'] = 'marierareagan@gmail.com'  # Change to your email

    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    mail.init_app(app)
    CORS(app)
    migrate = Migrate(app, db)

    # Create tables
    with app.app_context():
        db.create_all()

    # Registration route
    @app.route('/register', methods=['POST'])
    def register():
        data = request.json
        role = data.get('role')
        name = data.get('name')
        email = data.get('email')
        password = data.get('password')
        phone_number = data.get('phone_number')
        branch_name = data.get('branch_name')  # Get branch name for registration
        secret_password = data.get('secret_password')  # CEO secret password
        branch_ceo_secret = data.get('branch_ceo_secret')  # Branch CEO secret password

        # Role validation
        if role not in ['student', 'ceo', 'branch_ceo']:
            return jsonify({'message': 'Invalid role.'}), 400

        # Student registration
        if role == 'student':
            if Student.query.filter_by(email=email).first():
                return jsonify({'message': 'Student with this email already exists.'}), 400
            if Student.query.filter_by(nationality_number=data.get('nationality_number')).first():
                return jsonify({'message': 'Student with this nationality number already exists.'}), 400

            hashed_password = generate_password_hash(password)
            new_student = Student(
                name=name,
                email=email,
                password_hash=hashed_password,
                nationality_number=data.get('nationality_number'),
                branch_name=branch_name,
                phone_number=phone_number
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

            # Notify CEO about new student registration
            ceo_email = 'skynetdrivingschoolltd@gmail.com'  # Change to the actual CEO email
            if ceo_email:
                try:
                    msg = Message('New Student Registration', recipients=[ceo_email])
                    msg.body = f'A new student has registered.\nName: {name}\nEmail: {email}.'
                    mail.send(msg)
                except Exception as e:
                    return jsonify({'message': f'Failed to notify CEO: {str(e)}'}), 500

            return jsonify({'message': 'Student registered successfully.'}), 201

        # CEO registration
        elif role == 'ceo':
            if secret_password != 'SKYNETCEO':
                return jsonify({'message': 'Invalid secret password for CEO registration.'}), 400

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

        # Branch CEO registration
        elif role == 'branch_ceo':
            if branch_ceo_secret != 'BRANCHCEO2024':
                return jsonify({'message': 'Invalid secret password for Branch CEO registration.'}), 400

            if BranchCEO.query.filter_by(email=email).first():
                return jsonify({'message': 'Branch CEO with this email already exists.'}), 400

            hashed_password = generate_password_hash(password)
            new_branch_ceo = BranchCEO(
                name=name,
                email=email,
                password_hash=hashed_password,
                branch_name=branch_name  # Link Branch CEO to a branch using branch_name
            )
            db.session.add(new_branch_ceo)
            db.session.commit()

            # Notify current CEO about new Branch CEO registration
            ceo_email = 'skynetdrivingschoolltd@gmail.com'  # Change to actual CEO email
            try:
                msg = Message('New Branch CEO Registration', recipients=[ceo_email])
                msg.body = f'A new Branch CEO has registered.\nName: {name}\nEmail: {email}.'
                mail.send(msg)
            except Exception as e:
                return jsonify({'message': f'Failed to send notification email to CEO: {str(e)}'}), 500

            return jsonify({'message': 'Branch CEO registered successfully.'}), 201

        return jsonify({'message': 'Unknown error occurred.'}), 500

    # Login route
    @app.route('/login', methods=['POST'])
    def login():
        data = request.json
        email = data.get('email')
        password = data.get('password')

        student = Student.query.filter_by(email=email).first()
        ceo = CEO.query.filter_by(email=email).first()
        branch_ceo = BranchCEO.query.filter_by(email=email).first()

        user = student or ceo or branch_ceo
        if user and check_password_hash(user.password_hash, password):
            role = 'Branch CEO' if branch_ceo else 'CEO' if ceo else 'Student'
            access_token = create_access_token(identity={'id': user.id, 'role': role, 'branch_name': user.branch_name if hasattr(user, 'branch_name') else None})
            return jsonify({'access_token': access_token}), 200

        return jsonify({'message': 'Invalid credentials.'}), 401

    # Create student (Branch CEO access only)
    @app.route('/students', methods=['POST'])
    @jwt_required()
    def create_student():
        current_user = get_jwt_identity()
        if current_user['role'] != 'Branch CEO':
            return jsonify({'message': 'Unauthorized access.'}), 403

        data = request.json
        name = data.get('name')
        email = data.get('email')
        password = data.get('password')
        nationality_number = data.get('nationality_number')
        branch_name = current_user['branch_name']
        phone_number = data.get('phone_number')

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
            branch_name=branch_name,
            phone_number=phone_number,
            status='active'
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
                'branch': student.branch_name,
                'amount_paid': student.amount_paid,
                'top_up': student.top_up,
                'balance': student.balance,
                'phone_number': student.phone_number,
                'nationality_number': student.nationality_number,
                'status': student.status,
                'date_amount_paid_updated': student.date_amount_paid_updated.isoformat() if student.date_amount_paid_updated else None,
                'date_top_up_updated': student.date_top_up_updated.isoformat() if student.date_top_up_updated else None,
                'date_balance_updated': student.date_balance_updated.isoformat() if student.date_balance_updated else None,
                'last_updated': student.last_updated.isoformat() if student.last_updated else None
            }), 200

        return jsonify({'message': 'Student not found.'}), 404

    # Get all students for the current Branch CEO's branch
    @app.route('/students/branch', methods=['GET'])
    @jwt_required()
    def get_students_for_branch():
        current_user = get_jwt_identity()
        if current_user['role'] != 'Branch CEO':
            return jsonify({'message': 'Unauthorized access.'}), 403

        branch_name = current_user['branch_name']
        students = Student.query.filter_by(branch_name=branch_name).all()

        response = []
        for student in students:
            response.append({
                'id': student.id,
                'name': student.name,
                'email': student.email,
                'phone_number': student.phone_number,
                'nationality_number': student.nationality_number,
                'status': student.status,
                'amount_paid': student.amount_paid,
                'top_up': student.top_up,
                'balance': student.balance
            })

        return jsonify(response), 200

    # Get student by ID (CEO or Branch CEO access)
    @app.route('/students/<int:student_id>', methods=['GET'])
    @jwt_required()
    def get_student_by_id(student_id):
        current_user = get_jwt_identity()
        if current_user['role'] not in ['CEO', 'Branch CEO']:
            return jsonify({'message': 'Unauthorized access.'}), 403

        student = Student.query.get(student_id)
        if student:
            return jsonify({
                'id': student.id,
                'name': student.name,
                'email': student.email,
                'branch': student.branch_name,
                'amount_paid': student.amount_paid,
                'top_up': student.top_up,
                'balance': student.balance,
                'phone_number': student.phone_number,
                'nationality_number': student.nationality_number,
                'status': student.status,
                'date_amount_paid_updated': student.date_amount_paid_updated.isoformat() if student.date_amount_paid_updated else None,
                'date_top_up_updated': student.date_top_up_updated.isoformat() if student.date_top_up_updated else None,
                'date_balance_updated': student.date_balance_updated.isoformat() if student.date_balance_updated else None,
                'last_updated': student.last_updated.isoformat() if student.last_updated else None
            }), 200

        return jsonify({'message': 'Student not found.'}), 404

    # Update student (CEO or Branch CEO access)
    @app.route('/students/<int:student_id>', methods=['PUT'])
    @jwt_required()
    def update_student(student_id):
        current_user = get_jwt_identity()
        if current_user['role'] not in ['CEO', 'Branch CEO']:
            return jsonify({'message': 'Unauthorized access.'}), 403

        student = Student.query.get(student_id)
        if not student:
            return jsonify({'message': 'Student not found.'}), 404

        data = request.json
        if 'name' in data:
            student.name = data['name']
        if 'email' in data:
            student.email = data['email']
        if 'status' in data:
            student.status = data['status']
        if 'amount_paid' in data:
            student.amount_paid = data['amount_paid']
        if 'top_up' in data:
            student.top_up = data['top_up']
        if 'balance' in data:
            student.balance = data['balance']
        if 'phone_number' in data:
            student.phone_number = data['phone_number']
        if 'nationality_number' in data:
            student.nationality_number = data['nationality_number']

        student.last_updated = datetime.utcnow()  # Update the last_updated timestamp
        db.session.commit()

        return jsonify({'message': 'Student updated successfully.'}), 200

    # Delete student (CEO or Branch CEO access)
    @app.route('/students/<int:student_id>', methods=['DELETE'])
    @jwt_required()
    def delete_student(student_id):
        current_user = get_jwt_identity()
        if current_user['role'] not in ['CEO', 'Branch CEO']:
            return jsonify({'message': 'Unauthorized access.'}), 403

        student = Student.query.get(student_id)
        if student:
            db.session.delete(student)
            db.session.commit()
            return jsonify({'message': 'Student deleted successfully.'}), 200

        return jsonify({'message': 'Student not found.'}), 404

    # Create branch (for CEO)
    @app.route('/branches', methods=['POST'])
    @jwt_required()
    def create_branch():
        current_user = get_jwt_identity()
        if current_user['role'] != 'CEO':
            return jsonify({'message': 'Unauthorized access.'}), 403

        data = request.json
        branch_name = data.get('branch_name')

        new_branch = Branch(branch_name=branch_name)
        db.session.add(new_branch)
        db.session.commit()

        return jsonify({'message': 'Branch created successfully.'}), 201

    # Get branches (for CEO)
    @app.route('/branches', methods=['GET'])
    @jwt_required()
    def get_branches():
        current_user = get_jwt_identity()
        if current_user['role'] != 'CEO':
            return jsonify({'message': 'Unauthorized access.'}), 403

        branches = Branch.query.all()
        return jsonify([{'id': branch.id, 'branch_name': branch.branch_name} for branch in branches]), 200

    # Get all students (CEO access only)
    @app.route('/students/all', methods=['GET'])
    @jwt_required()
    def get_all_students():
        current_user = get_jwt_identity()
        if current_user['role'] != 'CEO':
            return jsonify({'message': 'Unauthorized access.'}), 403

        students = Student.query.all()  # Retrieve all students from the database

        response = []
        for student in students:
            response.append({
                'id': student.id,
                'name': student.name,
                'email': student.email,
                'branch': student.branch_name,
                'amount_paid': student.amount_paid,
                'top_up': student.top_up,
                'balance': student.balance,
                'phone_number': student.phone_number,
                'nationality_number': student.nationality_number,
                'status': student.status,
                'date_amount_paid_updated': student.date_amount_paid_updated.isoformat() if student.date_amount_paid_updated else None,
                'date_top_up_updated': student.date_top_up_updated.isoformat() if student.date_top_up_updated else None,
                'date_balance_updated': student.date_balance_updated.isoformat() if student.date_balance_updated else None,
                'last_updated': student.last_updated.isoformat() if student.last_updated else None
            })

        return jsonify(response), 200

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
