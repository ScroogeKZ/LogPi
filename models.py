from app import db
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import string
import random

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    password_hash = db.Column(db.String(256))
    role = db.Column(db.String(20), default='employee')  # employee, logist
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationship
    orders = db.relationship('Order', backref='customer', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_logist(self):
        return self.role == 'logist'
    
    def __repr__(self):
        return f'<User {self.email}>'

class Driver(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    vehicle_number = db.Column(db.String(20))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    orders = db.relationship('Order', backref='assigned_driver', lazy=True)
    
    def __repr__(self):
        return f'<Driver {self.full_name}>'

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tracking_number = db.Column(db.String(20), unique=True, nullable=False)
    
    # Customer information
    customer_name = db.Column(db.String(100), nullable=False)
    customer_phone = db.Column(db.String(20), nullable=False)
    customer_email = db.Column(db.String(120))
    customer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    # Order details
    order_type = db.Column(db.String(20), nullable=False)  # astana, kazakhstan
    pickup_address = db.Column(db.Text, nullable=False)
    pickup_contact = db.Column(db.String(100))
    pickup_phone = db.Column(db.String(20))
    
    delivery_address = db.Column(db.Text, nullable=False)
    delivery_contact = db.Column(db.String(100))
    delivery_phone = db.Column(db.String(20))
    
    cargo_description = db.Column(db.Text, nullable=False)
    cargo_weight = db.Column(db.Float)
    cargo_volume = db.Column(db.Float)
    cargo_dimensions = db.Column(db.String(100))
    
    # Order status and management
    status = db.Column(db.String(20), default='new')  # new, confirmed, in_progress, delivered, cancelled
    price = db.Column(db.Float)
    driver_id = db.Column(db.Integer, db.ForeignKey('driver.id'), nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    pickup_date = db.Column(db.DateTime)
    delivery_date = db.Column(db.DateTime)
    
    # Internal comments
    internal_comments = db.Column(db.Text)
    
    def __init__(self, **kwargs):
        super(Order, self).__init__(**kwargs)
        if not self.tracking_number:
            self.tracking_number = self.generate_tracking_number()
    
    @staticmethod
    def generate_tracking_number():
        """Generate unique tracking number in format AST-YYYY-XXX or KZ-YYYY-XXX"""
        while True:
            year = datetime.now().year
            random_part = ''.join(random.choices(string.digits, k=3))
            tracking_number = f"AST-{year}-{random_part}"
            
            # Check if tracking number already exists
            if not Order.query.filter_by(tracking_number=tracking_number).first():
                return tracking_number
    
    def get_status_display(self):
        status_map = {
            'new': 'Новая заявка',
            'confirmed': 'Подтверждена',
            'in_progress': 'В процессе доставки',
            'delivered': 'Доставлена',
            'cancelled': 'Отменена'
        }
        return status_map.get(self.status, self.status)
    
    def get_type_display(self):
        type_map = {
            'astana': 'Доставка по Астане',
            'kazakhstan': 'Межгородская перевозка'
        }
        return type_map.get(self.order_type, self.order_type)
    
    def __repr__(self):
        return f'<Order {self.tracking_number}>'

class OrderStatusHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    comment = db.Column(db.Text)
    changed_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    order = db.relationship('Order', backref=db.backref('status_history', lazy=True))
    changed_by = db.relationship('User', backref='status_changes')
    
    def __repr__(self):
        return f'<OrderStatusHistory {self.order_id}: {self.status}>'
