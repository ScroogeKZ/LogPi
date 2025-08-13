from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, FloatField, PasswordField, DateTimeField, HiddenField
from wtforms.validators import DataRequired, Email, Length, Optional, NumberRange
from wtforms.widgets import TextArea
from models import Driver

class OrderForm(FlaskForm):
    # Customer information
    customer_name = StringField('Ф.И.О.', validators=[DataRequired(), Length(min=2, max=100)])
    customer_phone = StringField('Номер телефона', validators=[DataRequired(), Length(min=10, max=20)])
    
    # Pickup details
    pickup_address = TextAreaField('Адрес погрузки', validators=[DataRequired()], widget=TextArea())
    pickup_contact = StringField('Контактное лицо (погрузка)', validators=[Optional(), Length(max=100)])
    pickup_phone = StringField('Телефон (погрузка)', validators=[Optional(), Length(max=20)])
    
    # Delivery details
    delivery_address = TextAreaField('Адрес выгрузки', validators=[DataRequired()], widget=TextArea())
    delivery_contact = StringField('Контактное лицо (выгрузка)', validators=[Optional(), Length(max=100)])
    delivery_phone = StringField('Телефон (выгрузка)', validators=[Optional(), Length(max=20)])
    
    # Cargo details
    cargo_description = TextAreaField('Описание груза', validators=[DataRequired()], widget=TextArea())
    cargo_weight = FloatField('Вес груза (кг)', validators=[Optional(), NumberRange(min=0)])
    cargo_volume = FloatField('Объем груза (м³)', validators=[Optional(), NumberRange(min=0)])
    cargo_dimensions = StringField('Габариты груза', validators=[Optional(), Length(max=100)])
    
    # Hidden field for order type
    order_type = HiddenField()

class TrackingForm(FlaskForm):
    tracking_number = StringField('Номер заявки', validators=[DataRequired()], 
                                render_kw={"placeholder": "Введите номер заявки (например: AST-2025-001)"})

class RegistrationForm(FlaskForm):
    full_name = StringField('Полное имя', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Номер телефона', validators=[DataRequired(), Length(min=10, max=20)])
    password = PasswordField('Пароль', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Подтвердите пароль', validators=[DataRequired()])

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired()])

class AdminOrderForm(FlaskForm):
    status = SelectField('Статус заказа', choices=[
        ('new', 'Новая заявка'),
        ('confirmed', 'Подтверждена'),
        ('in_progress', 'В процессе доставки'),
        ('delivered', 'Доставлена'),
        ('cancelled', 'Отменена')
    ])
    price = FloatField('Стоимость доставки', validators=[Optional(), NumberRange(min=0)])
    driver_id = SelectField('Водитель', coerce=int, validators=[Optional()])
    internal_comments = TextAreaField('Внутренние комментарии', validators=[Optional()], widget=TextArea())
    pickup_date = DateTimeField('Дата забора', validators=[Optional()], format='%Y-%m-%dT%H:%M')
    delivery_date = DateTimeField('Дата доставки', validators=[Optional()], format='%Y-%m-%dT%H:%M')
    
    def __init__(self, *args, **kwargs):
        super(AdminOrderForm, self).__init__(*args, **kwargs)
        # Populate driver choices
        drivers = Driver.query.filter_by(active=True).all()
        self.driver_id.choices = [(0, 'Не назначен')] + [(d.id, f"{d.full_name} ({d.vehicle_number})") for d in drivers]

class DriverForm(FlaskForm):
    full_name = StringField('Полное имя', validators=[DataRequired(), Length(min=2, max=100)])
    phone = StringField('Номер телефона', validators=[DataRequired(), Length(min=10, max=20)])
    vehicle_number = StringField('Номер автомобиля', validators=[Optional(), Length(max=20)])
