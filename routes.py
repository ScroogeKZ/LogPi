from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app import app, db
from models import User, Order, Driver, OrderStatusHistory
from forms import OrderForm, TrackingForm, RegistrationForm, LoginForm, AdminOrderForm, DriverForm
from werkzeug.security import generate_password_hash
from telegram_bot import send_telegram_notification
from datetime import datetime, timedelta
from sqlalchemy import func, extract
import logging

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/order/<order_type>')
def create_order(order_type):
    if order_type not in ['astana', 'kazakhstan']:
        flash('Неверный тип заказа', 'error')
        return redirect(url_for('index'))
    
    form = OrderForm()
    form.order_type.data = order_type
    
    order_title = 'Доставка по Астане' if order_type == 'astana' else 'Межгородская перевозка'
    
    return render_template('order_form.html', form=form, order_type=order_type, order_title=order_title)

@app.route('/submit_order', methods=['POST'])
def submit_order():
    form = OrderForm()
    
    if form.validate_on_submit():
        try:
            # Create new order
            order = Order(
                customer_name=form.customer_name.data,
                customer_phone=form.customer_phone.data,
                customer_email=form.customer_email.data,
                order_type=form.order_type.data,
                pickup_address=form.pickup_address.data,
                pickup_contact=form.pickup_contact.data,
                pickup_phone=form.pickup_phone.data,
                delivery_address=form.delivery_address.data,
                delivery_contact=form.delivery_contact.data,
                delivery_phone=form.delivery_phone.data,
                cargo_description=form.cargo_description.data,
                cargo_weight=form.cargo_weight.data,
                cargo_volume=form.cargo_volume.data,
                cargo_dimensions=form.cargo_dimensions.data
            )
            
            # If user is logged in, associate order with user
            if current_user.is_authenticated:
                order.customer_id = current_user.id
            
            db.session.add(order)
            db.session.commit()
            
            # Send Telegram notification
            try:
                send_telegram_notification(order)
            except Exception as e:
                logging.error(f"Failed to send Telegram notification: {e}")
            
            flash(f'Заявка успешно создана! Ваш номер отслеживания: {order.tracking_number}', 'success')
            return redirect(url_for('order_success', tracking_number=order.tracking_number))
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error creating order: {e}")
            flash('Произошла ошибка при создании заявки. Попробуйте еще раз.', 'error')
    
    # If validation failed, show form with errors
    order_type = form.order_type.data or 'astana'
    order_title = 'Доставка по Астане' if order_type == 'astana' else 'Межгородская перевозка'
    
    return render_template('order_form.html', form=form, order_type=order_type, order_title=order_title)

@app.route('/order_success/<tracking_number>')
def order_success(tracking_number):
    order = Order.query.filter_by(tracking_number=tracking_number).first()
    if not order:
        flash('Заказ не найден', 'error')
        return redirect(url_for('index'))
    
    return render_template('order_status.html', order=order, success_page=True)

@app.route('/track')
def track_order():
    form = TrackingForm()
    return render_template('track_order.html', form=form)

@app.route('/track_result', methods=['POST'])
def track_result():
    # Handle tracking request directly from form data
    tracking_number = request.form.get('tracking_number', '').strip()
    
    if tracking_number:
        tracking_number = tracking_number.upper()
        order = Order.query.filter_by(tracking_number=tracking_number).first()
        
        if order:
            return render_template('order_status.html', order=order)
        else:
            flash('Заказ с указанным номером не найден', 'error')
    else:
        flash('Пожалуйста, введите номер заявки', 'error')
    
    # Return to homepage if validation fails
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('profile'))
    
    form = RegistrationForm()
    
    if form.validate_on_submit():
        # Check if passwords match
        if form.password.data != form.confirm_password.data:
            flash('Пароли не совпадают', 'error')
            return render_template('register.html', form=form)
        
        # Check if user already exists
        if User.query.filter_by(email=form.email.data).first():
            flash('Пользователь с таким email уже существует', 'error')
            return render_template('register.html', form=form)
        
        # Create new user
        user = User(
            full_name=form.full_name.data,
            email=form.email.data,
            phone=form.phone.data
        )
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()
        
        # Associate existing orders with this user
        existing_orders = Order.query.filter_by(customer_phone=user.phone, customer_id=None).all()
        for order in existing_orders:
            order.customer_id = user.id
        db.session.commit()
        
        login_user(user)
        flash('Регистрация успешна! Добро пожаловать в систему XPOM-KZ', 'success')
        return redirect(url_for('profile'))
    
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('profile'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        
        if user and user.check_password(form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('profile'))
        else:
            flash('Неверный email или пароль', 'error')
    
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы успешно вышли из системы', 'info')
    return redirect(url_for('index'))

@app.route('/profile')
@login_required
def profile():
    orders = Order.query.filter_by(customer_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template('profile.html', orders=orders)

# Admin routes
@app.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_logist():
        flash('У вас нет прав доступа к административной панели', 'error')
        return redirect(url_for('index'))
    
    # Get statistics
    total_orders = Order.query.count()
    new_orders = Order.query.filter_by(status='new').count()
    in_progress_orders = Order.query.filter_by(status='in_progress').count()
    delivered_orders = Order.query.filter_by(status='delivered').count()
    
    # Recent orders
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(10).all()
    
    stats = {
        'total_orders': total_orders,
        'new_orders': new_orders,
        'in_progress_orders': in_progress_orders,
        'delivered_orders': delivered_orders
    }
    
    return render_template('admin/dashboard.html', stats=stats, recent_orders=recent_orders)

@app.route('/admin/orders')
@login_required
def admin_orders():
    if not current_user.is_logist():
        flash('У вас нет прав доступа к административной панели', 'error')
        return redirect(url_for('index'))
    
    # Get filter parameters
    status_filter = request.args.get('status', '')
    order_type_filter = request.args.get('type', '')
    
    # Build query
    query = Order.query
    
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    if order_type_filter:
        query = query.filter_by(order_type=order_type_filter)
    
    orders = query.order_by(Order.created_at.desc()).all()
    
    return render_template('admin/orders.html', orders=orders, 
                         status_filter=status_filter, order_type_filter=order_type_filter)

@app.route('/admin/order/<int:order_id>')
@login_required
def admin_order_detail(order_id):
    if not current_user.is_logist():
        flash('У вас нет прав доступа к административной панели', 'error')
        return redirect(url_for('index'))
    
    order = Order.query.get_or_404(order_id)
    form = AdminOrderForm(obj=order)
    
    # Set driver_id to 0 if None for form display
    if not order.driver_id:
        form.driver_id.data = 0
    
    return render_template('admin/order_detail.html', order=order, form=form)

@app.route('/admin/order/<int:order_id>/update', methods=['POST'])
@login_required
def admin_update_order(order_id):
    if not current_user.is_logist():
        flash('У вас нет прав доступа к административной панели', 'error')
        return redirect(url_for('index'))
    
    order = Order.query.get_or_404(order_id)
    form = AdminOrderForm()
    
    if form.validate_on_submit():
        # Track status change
        old_status = order.status
        new_status = form.status.data
        
        # Update order
        order.status = new_status
        order.price = form.price.data
        order.internal_comments = form.internal_comments.data
        order.pickup_date = form.pickup_date.data
        order.delivery_date = form.delivery_date.data
        order.updated_at = datetime.utcnow()
        
        # Handle driver assignment
        if form.driver_id.data and form.driver_id.data != 0:
            order.driver_id = form.driver_id.data
        else:
            order.driver_id = None
        
        # Add status history if status changed
        if old_status != new_status:
            history = OrderStatusHistory(
                order_id=order.id,
                status=new_status,
                comment=f"Статус изменен с '{order.get_status_display()}' на '{form.status.data}'",
                changed_by_id=current_user.id
            )
            db.session.add(history)
        
        db.session.commit()
        flash('Заказ успешно обновлен', 'success')
        
    return redirect(url_for('admin_order_detail', order_id=order_id))

@app.route('/admin/reports')
@login_required
def admin_reports():
    if not current_user.is_logist():
        flash('У вас нет прав доступа к административной панели', 'error')
        return redirect(url_for('index'))
    
    # Get date range (default: last 30 days)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    # Basic statistics
    total_orders = Order.query.filter(Order.created_at >= start_date).count()
    total_revenue = db.session.query(func.sum(Order.price)).filter(
        Order.created_at >= start_date, Order.price.isnot(None)
    ).scalar() or 0
    
    avg_cost = total_revenue / total_orders if total_orders > 0 else 0
    
    # Orders by type
    astana_orders = Order.query.filter(
        Order.created_at >= start_date, Order.order_type == 'astana'
    ).count()
    kz_orders = Order.query.filter(
        Order.created_at >= start_date, Order.order_type == 'kazakhstan'
    ).count()
    
    # Driver statistics
    driver_stats = db.session.query(
        Driver.full_name,
        func.count(Order.id).label('order_count'),
        func.sum(Order.price).label('total_cost')
    ).join(Order, Driver.id == Order.driver_id).filter(
        Order.created_at >= start_date
    ).group_by(Driver.id, Driver.full_name).all()
    
    stats = {
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'avg_cost': avg_cost,
        'astana_orders': astana_orders,
        'kz_orders': kz_orders,
        'driver_stats': driver_stats,
        'period': f"{start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}"
    }
    
    return render_template('admin/reports.html', stats=stats)

@app.route('/admin/analytics')
@login_required
def admin_analytics():
    if not current_user.is_logist():
        flash('У вас нет прав доступа к административной панели', 'error')
        return redirect(url_for('index'))
    
    # Get monthly order data for the last 12 months
    monthly_data = []
    for i in range(11, -1, -1):
        date = datetime.now().replace(day=1) - timedelta(days=i*30)
        month_start = date.replace(day=1)
        if i == 0:
            month_end = datetime.now()
        else:
            next_month = month_start.replace(month=month_start.month+1) if month_start.month < 12 else month_start.replace(year=month_start.year+1, month=1)
            month_end = next_month - timedelta(days=1)
        
        order_count = Order.query.filter(
            Order.created_at >= month_start,
            Order.created_at <= month_end
        ).count()
        
        revenue = db.session.query(func.sum(Order.price)).filter(
            Order.created_at >= month_start,
            Order.created_at <= month_end,
            Order.price.isnot(None)
        ).scalar() or 0
        
        monthly_data.append({
            'month': month_start.strftime('%Y-%m'),
            'month_name': month_start.strftime('%B %Y'),
            'orders': order_count,
            'revenue': float(revenue)
        })
    
    # Status distribution
    status_data = []
    statuses = ['new', 'confirmed', 'in_progress', 'delivered', 'cancelled']
    for status in statuses:
        count = Order.query.filter_by(status=status).count()
        status_data.append({
            'status': status,
            'count': count,
            'label': Order().get_status_display() if status == 'new' else {
                'confirmed': 'Подтверждена',
                'in_progress': 'В процессе доставки',
                'delivered': 'Доставлена',
                'cancelled': 'Отменена'
            }.get(status, status)
        })
    
    return render_template('admin/analytics.html', 
                         monthly_data=monthly_data, 
                         status_data=status_data)

@app.route('/api/orders_chart_data')
@login_required
def orders_chart_data():
    if not current_user.is_logist():
        return jsonify({'error': 'Access denied'}), 403
    
    # Get last 7 days data
    data = []
    for i in range(6, -1, -1):
        date = datetime.now().date() - timedelta(days=i)
        order_count = Order.query.filter(
            func.date(Order.created_at) == date
        ).count()
        
        data.append({
            'date': date.strftime('%d.%m'),
            'orders': order_count
        })
    
    return jsonify(data)

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500
