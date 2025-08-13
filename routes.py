from flask import render_template, request, redirect, url_for, flash, jsonify, send_file, make_response
from flask_login import login_user, logout_user, login_required, current_user
from app import app, db
from models import User, Order, Driver, OrderStatusHistory
from forms import OrderForm, TrackingForm, RegistrationForm, LoginForm, AdminOrderForm, DriverForm
from werkzeug.security import generate_password_hash
from telegram_bot import send_telegram_notification
from datetime import datetime, timedelta
from sqlalchemy import func, extract
import logging
import csv
from io import StringIO

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
                customer_email=None,  # Email field removed from form
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
    drivers = Driver.query.filter_by(active=True).all()
    
    return render_template('admin/order_detail.html', order=order, drivers=drivers)

@app.route('/admin/order/<int:order_id>/update', methods=['POST'])
@login_required
def admin_update_order(order_id):
    if not current_user.is_logist():
        flash('У вас нет прав доступа к административной панели', 'error')
        return redirect(url_for('index'))
    
    try:
        order = Order.query.get_or_404(order_id)
        
        # Update order fields
        order.status = request.form.get('status')
        order.internal_comments = request.form.get('internal_comments')
        
        # Only logists can update price and driver assignment
        if current_user.is_logist():
            order.price = float(request.form.get('price')) if request.form.get('price') else None
            
            # Handle driver assignment
            driver_id = request.form.get('driver_id')
            if driver_id and driver_id != '0':
                order.driver_id = int(driver_id)
            else:
                order.driver_id = None
            
        order.updated_at = datetime.utcnow()
        
        db.session.commit()
        flash('Заказ успешно обновлен', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash('Ошибка при обновлении заказа', 'error')
        
    return redirect(url_for('admin_order_detail', order_id=order_id))

@app.route('/admin/order/<int:order_id>/complete', methods=['POST'])
@login_required
def admin_complete_order(order_id):
    if not current_user.is_logist():
        flash('У вас нет прав доступа к административной панели', 'error')
        return redirect(url_for('index'))
    
    try:
        order = Order.query.get_or_404(order_id)
        order.status = 'delivered'
        order.delivery_date = datetime.utcnow()
        order.updated_at = datetime.utcnow()
        
        db.session.commit()
        flash('Заказ отмечен как выполненный', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash('Ошибка при обновлении заказа', 'error')
        
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

@app.route('/admin/financial_reports')
@login_required
def admin_financial_reports():
    if not current_user.is_logist():
        flash('У вас нет прав доступа к финансовым отчётам', 'error')
        return redirect(url_for('index'))
    
    # Get filter parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    order_type = request.args.get('order_type')
    export_format = request.args.get('export')
    
    # Set default date range (last 30 days)
    if not start_date or not end_date:
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)
    else:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    # Build query
    query = Order.query.filter(
        Order.created_at >= start_date,
        Order.created_at <= end_date + timedelta(days=1),
        Order.price.isnot(None)
    )
    
    if order_type:
        query = query.filter_by(order_type=order_type)
    
    orders = query.all()
    
    # Calculate summary statistics (expenses for the company)
    total_expenses = sum(order.price for order in orders if order.price)
    total_orders = len(orders)
    avg_order_value = total_expenses / total_orders if total_orders > 0 else 0
    active_drivers = Driver.query.filter_by(active=True).count()
    
    # Expenses by type (company logistics costs)
    expenses_by_type = {}
    for order in orders:
        order_type_key = order.order_type
        if order_type_key not in expenses_by_type:
            expenses_by_type[order_type_key] = 0
        expenses_by_type[order_type_key] += order.price or 0
    
    revenue_by_type_labels = ['Астана' if k == 'astana' else 'Казахстан' for k in expenses_by_type.keys()]
    revenue_by_type_data = list(expenses_by_type.values())
    
    # Monthly expenses data
    monthly_expenses = {}
    for order in orders:
        month_key = order.created_at.strftime('%Y-%m')
        if month_key not in monthly_expenses:
            monthly_expenses[month_key] = 0
        monthly_expenses[month_key] += order.price or 0
    
    monthly_labels = [datetime.strptime(k, '%Y-%m').strftime('%b %Y') for k in sorted(monthly_expenses.keys())]
    monthly_revenue_data = [monthly_expenses[k] for k in sorted(monthly_expenses.keys())]
    
    # Top drivers by service costs (company expenses)
    driver_stats = {}
    for order in orders:
        if order.assigned_driver:
            driver_id = order.assigned_driver.id
            if driver_id not in driver_stats:
                driver_stats[driver_id] = {
                    'name': order.assigned_driver.full_name,
                    'order_count': 0,
                    'revenue': 0  # keeping key name for template compatibility
                }
            driver_stats[driver_id]['order_count'] += 1
            driver_stats[driver_id]['revenue'] += order.price or 0
    
    top_drivers = sorted(driver_stats.values(), key=lambda x: x['revenue'], reverse=True)[:5]
    
    # Weekly expenses statistics
    weekly_stats = {}
    for order in orders:
        day_name = order.created_at.strftime('%A')
        day_name_ru = {
            'Monday': 'Понедельник',
            'Tuesday': 'Вторник', 
            'Wednesday': 'Среда',
            'Thursday': 'Четверг',
            'Friday': 'Пятница',
            'Saturday': 'Суббота',
            'Sunday': 'Воскресенье'
        }.get(day_name, day_name)
        
        if day_name_ru not in weekly_stats:
            weekly_stats[day_name_ru] = {'day_name': day_name_ru, 'order_count': 0, 'revenue': 0}  # keeping key name for template compatibility
        weekly_stats[day_name_ru]['order_count'] += 1
        weekly_stats[day_name_ru]['revenue'] += order.price or 0
    
    weekly_stats = list(weekly_stats.values())
    
    # Export to CSV if requested
    if export_format == 'excel':
        return generate_csv_report(orders, start_date, end_date)
    
    return render_template('admin/financial_reports.html',
                         start_date=start_date,
                         end_date=end_date,
                         order_type=order_type,
                         total_revenue=total_expenses,
                         total_orders=total_orders,
                         avg_order_value=avg_order_value,
                         active_drivers=active_drivers,
                         revenue_by_type_labels=revenue_by_type_labels,
                         revenue_by_type_data=revenue_by_type_data,
                         monthly_labels=monthly_labels,
                         monthly_revenue_data=monthly_revenue_data,
                         top_drivers=top_drivers,
                         weekly_stats=weekly_stats)

def generate_csv_report(orders, start_date, end_date):
    """Generate CSV report for financial data"""
    output = StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        'Номер заказа', 'Дата создания', 'Клиент', 'Направление', 
        'Откуда', 'Куда', 'Статус', 'Водитель', 'Стоимость'
    ])
    
    # Write data
    for order in orders:
        writer.writerow([
            order.tracking_number,
            order.created_at.strftime('%d.%m.%Y %H:%M'),
            order.customer_name,
            'Астана' if order.order_type == 'astana' else 'Казахстан',
            order.pickup_address,
            order.delivery_address,
            order.get_status_display(),
            order.assigned_driver.full_name if order.assigned_driver else 'Не назначен',
            f'{order.price:.0f}' if order.price else '0'
        ])
    
    # Prepare response
    output.seek(0)
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    response.headers['Content-Disposition'] = f'attachment; filename=financial_report_{start_date}_{end_date}.csv'
    
    return response

@app.route('/admin/calendar')
@login_required
def admin_calendar():
    if not current_user.is_logist():
        flash('У вас нет прав доступа к административной панели', 'error')
        return redirect(url_for('index'))
    
    # Get orders without scheduled dates for planning
    available_orders = Order.query.filter(
        Order.status.in_(['new', 'confirmed']),
        Order.scheduled_pickup_date.is_(None)
    ).all()
    
    # Get active drivers
    drivers = Driver.query.filter(Driver.active == True).all()
    
    return render_template('admin/calendar.html', 
                         available_orders=available_orders, 
                         drivers=drivers)

@app.route('/admin/calendar/events')
@login_required  
def admin_calendar_events():
    if not current_user.is_logist():
        return jsonify({'error': 'Access denied'}), 403
    
    # Get orders with scheduled dates
    orders = Order.query.filter(
        db.or_(
            Order.scheduled_pickup_date.isnot(None),
            Order.scheduled_delivery_date.isnot(None)
        )
    ).all()
    
    events = []
    
    for order in orders:
        # Pickup event
        if order.scheduled_pickup_date:
            event_type = 'pickup'
            if order.status == 'cancelled':
                event_type = 'cancelled'
            elif order.scheduled_pickup_date < datetime.now().date() and order.status != 'delivered':
                event_type = 'overdue'
                
            events.append({
                'id': f'pickup_{order.id}',
                'title': f'Забор: {order.tracking_number}',
                'start': order.scheduled_pickup_date.isoformat(),
                'backgroundColor': '#3b82f6' if event_type == 'pickup' else ('#f59e0b' if event_type == 'overdue' else '#ef4444'),
                'borderColor': '#3b82f6' if event_type == 'pickup' else ('#f59e0b' if event_type == 'overdue' else '#ef4444'),
                'extendedProps': {
                    'order_id': order.id,
                    'type': event_type,
                    'event_type': 'pickup'
                }
            })
        
        # Delivery event  
        if order.scheduled_delivery_date:
            event_type = 'delivery'
            if order.status == 'cancelled':
                event_type = 'cancelled'
            elif order.scheduled_delivery_date < datetime.now().date() and order.status != 'delivered':
                event_type = 'overdue'
                
            events.append({
                'id': f'delivery_{order.id}',
                'title': f'Доставка: {order.tracking_number}',
                'start': order.scheduled_delivery_date.isoformat(),
                'backgroundColor': '#10b981' if event_type == 'delivery' else ('#f59e0b' if event_type == 'overdue' else '#ef4444'),
                'borderColor': '#10b981' if event_type == 'delivery' else ('#f59e0b' if event_type == 'overdue' else '#ef4444'),
                'extendedProps': {
                    'order_id': order.id,
                    'type': event_type,
                    'event_type': 'delivery'
                }
            })
    
    return jsonify(events)

@app.route('/admin/calendar/event/<int:order_id>')
@login_required
def admin_calendar_event_details(order_id):
    if not current_user.is_logist():
        return jsonify({'error': 'Access denied'}), 403
    
    order = Order.query.get_or_404(order_id)
    
    return jsonify({
        'tracking_number': order.tracking_number,
        'customer_name': order.customer_name,
        'customer_phone': order.customer_phone,
        'order_type': order.order_type,
        'driver_name': order.assigned_driver.full_name if order.assigned_driver else None,
        'scheduled_pickup_date': order.scheduled_pickup_date.strftime('%d.%m.%Y') if order.scheduled_pickup_date else None,
        'scheduled_delivery_date': order.scheduled_delivery_date.strftime('%d.%m.%Y') if order.scheduled_delivery_date else None,
        'pickup_address': order.pickup_address,
        'delivery_address': order.delivery_address,
        'status': order.status,
        'status_display': order.get_status_display()
    })

@app.route('/admin/schedule_shipment', methods=['POST'])
@login_required
def admin_schedule_shipment():
    if not current_user.is_logist():
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        order_id = request.form.get('order_id')
        driver_id = request.form.get('driver_id')
        pickup_date = datetime.strptime(request.form.get('pickup_date'), '%Y-%m-%d').date()
        delivery_date = datetime.strptime(request.form.get('delivery_date'), '%Y-%m-%d').date()
        
        order = Order.query.get_or_404(order_id)
        
        # Update order with scheduled dates
        order.scheduled_pickup_date = pickup_date
        order.scheduled_delivery_date = delivery_date
        order.driver_id = driver_id
        order.status = 'confirmed'
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Отгрузка запланирована успешно'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Ошибка при планировании отгрузки'})

@app.route('/admin/orders/<int:order_id>/complete', methods=['POST'])
@login_required
def admin_complete_order_old(order_id):
    if not current_user.is_logist():
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        order = Order.query.get_or_404(order_id)
        order.status = 'delivered'
        order.actual_delivery_date = datetime.now().date()
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Заказ отмечен как выполненный'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Ошибка при обновлении статуса'})

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500
