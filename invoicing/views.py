from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail, EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
from django.http import HttpResponse
from .models import Service, ServiceCategory, Package, Invoice, InvoiceItem
import qrcode
from io import BytesIO
from django.core.files import File
from decimal import Decimal
from datetime import datetime
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.utils import timezone
from django.db.models import Sum, Q
from parking.models import Reservation
from carwash.models import CarWashService
from users.mixins import RoleRequiredMixin
from payments.models import Payment
from django.views.decorators.http import require_POST
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# Create your views here.

@login_required
def billing_view(request):
    categories = ServiceCategory.objects.all()
    services = Service.objects.filter(is_active=True)
    packages = Package.objects.filter(is_active=True)
    
    if request.method == 'POST':
        # Get selected services and packages
        selected_services = request.POST.getlist('services')
        selected_packages = request.POST.getlist('packages')
        client_name = request.POST.get('client_name', '')
        payment_method = request.POST.get('payment_method')
        
        # Calculate totals
        subtotal = Decimal('0.00')
        services_list = []
        packages_list = []
        
        # Add individual services
        for service_id in selected_services:
            service = Service.objects.get(id=service_id)
            subtotal += service.price
            services_list.append(service)
        
        # Add packages
        for package_id in selected_packages:
            package = Package.objects.get(id=package_id)
            subtotal += package.discounted_price
            packages_list.append(package)
        
        # Calculate tax (16% IVA)
        tax = subtotal * Decimal('0.16')
        total = subtotal + tax
        
        # Create invoice
        invoice = Invoice.objects.create(
            client=request.user if request.user.is_authenticated else None,
            client_name=client_name,
            subtotal=subtotal,
            tax=tax,
            total=total,
            payment_method=payment_method
        )
        
        # Add services and packages to invoice
        invoice.services.set(services_list)
        invoice.packages.set(packages_list)
        
        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(str(invoice.invoice_number))
        qr.make(fit=True)
        qr_image = qr.make_image(fill_color="black", back_color="white")
        
        # Save QR code
        buffer = BytesIO()
        qr_image.save(buffer, format='PNG')
        invoice.qr_code.save(f'qr_{invoice.invoice_number}.png', File(buffer), save=True)
        
        # Send email if requested
        if request.POST.get('send_email'):
            context = {
                'invoice': invoice,
                'services': services_list,
                'packages': packages_list,
            }
            html_message = render_to_string('invoicing/email/invoice.html', context)
            send_mail(
                f'Factura #{invoice.invoice_number} - Park & Wash',
                'Gracias por su compra',
                settings.DEFAULT_FROM_EMAIL,
                [request.user.email],
                html_message=html_message
            )
        
        messages.success(request, 'Factura generada exitosamente')
        return redirect('invoicing:invoice_detail', invoice_id=invoice.id)
    
    context = {
        'categories': categories,
        'services': services,
        'packages': packages,
    }
    return render(request, 'invoicing/billing.html', context)

@login_required
def invoice_detail(request, invoice_id):
    invoice = Invoice.objects.get(id=invoice_id)
    context = {
        'invoice': invoice,
        'services': invoice.services.all(),
        'packages': invoice.packages.all(),
    }
    return render(request, 'invoicing/invoice_detail.html', context)

@login_required
def download_invoice_txt(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    
    # Create text content
    content = []
    content.append("=" * 50)
    content.append("PARK & WASH")
    content.append("Tu solución integral para estacionamiento y lavado de autos")
    content.append("=" * 50)
    content.append(f"\nFactura #{invoice.invoice_number}")
    content.append(f"Fecha: {invoice.date_created.strftime('%d/%m/%Y %H:%M')}")
    
    # Client information
    content.append("\nINFORMACIÓN DEL CLIENTE")
    content.append("-" * 30)
    if invoice.user:
        content.append(f"Cliente: {invoice.user.get_full_name() or invoice.user.username}")
        content.append(f"Email: {invoice.user.email}")
    else:
        content.append("Cliente: Cliente General")
    
    # Payment information
    content.append("\nINFORMACIÓN DE PAGO")
    content.append("-" * 30)
    content.append(f"Método de Pago: {invoice.get_payment_method_display()}")
    content.append(f"Estado: {invoice.get_status_display()}")
    
    # Items
    content.append("\nITEMS")
    content.append("-" * 30)
    
    # Calculate totals
    subtotal = Decimal('0.00')
    for item in invoice.items.all():
        content.append(f"- {item.description}")
        content.append(f"  Cantidad: {item.quantity}")
        content.append(f"  Precio Unitario: ${item.unit_price}")
        content.append(f"  Total: ${item.total_price}")
        content.append("")
        subtotal += item.total_price
    
    # Calculate tax (16% IVA)
    tax = subtotal * Decimal('0.16')
    total = subtotal + tax
    
    # Totals
    content.append("\nTOTALES")
    content.append("-" * 30)
    content.append(f"Subtotal: ${subtotal:.2f}")
    content.append(f"IVA (16%): ${tax:.2f}")
    content.append(f"Total: ${total:.2f}")
    
    # Footer
    content.append("\n" + "=" * 50)
    content.append("Gracias por su preferencia")
    content.append("Park & Wash - Todos los derechos reservados")
    content.append("=" * 50)
    
    # Create response
    response = HttpResponse('\n'.join(content), content_type='text/plain')
    response['Content-Disposition'] = f'attachment; filename="factura_{invoice.invoice_number}.txt"'
    
    return response

class InvoiceListView(LoginRequiredMixin, ListView):
    model = Invoice
    template_name = 'invoicing/invoice_list.html'
    context_object_name = 'invoices'

    def get_queryset(self):
        # Filtrar facturas por usuario si no es staff
        qs = Invoice.objects.all() if self.request.user.is_staff else Invoice.objects.filter(user=self.request.user)
        
        # Aplicar filtros adicionales
        status = self.request.GET.get('status')
        payment_method = self.request.GET.get('payment_method')
        
        if status:
            qs = qs.filter(status=status)
        if payment_method:
            qs = qs.filter(payment_method=payment_method)
            
        # Actualizar estado de la factura basado en los pagos
        for invoice in qs:
            reservation_ids = invoice.items.filter(reservation__isnull=False).values_list('reservation__id', flat=True)
            appointment_ids = invoice.items.filter(carwash_service__isnull=False).values_list('carwash_service__appointment__id', flat=True)
            pagos = Payment.objects.filter(
                Q(reservation__id__in=reservation_ids) | Q(appointment__id__in=appointment_ids),
                status='COMPLETED'
            ).distinct()
            # Solo marcar como PAID si hay pagos, pero nunca regresar a PENDING si ya está en PAID
            if pagos.exists() and invoice.status != 'PAID':
                invoice.status = 'PAID'
                invoice.save()
        return qs.order_by('-date_created')

class InvoiceDetailView(LoginRequiredMixin, DetailView):
    model = Invoice
    template_name = 'invoicing/invoice_detail.html'
    context_object_name = 'invoice'

    def get_queryset(self):
        if self.request.user.is_staff:
            return Invoice.objects.all()
        return Invoice.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        invoice = self.get_object()
        
        # Obtener los IDs de las reservas y citas relacionadas con esta factura
        reservation_ids = invoice.items.filter(reservation__isnull=False).values_list('reservation__id', flat=True)
        appointment_ids = invoice.items.filter(carwash_service__isnull=False).values_list('carwash_service__appointment__id', flat=True)
        
        # Buscar pagos relacionados con estas reservas y citas
        pagos = Payment.objects.filter(
            Q(reservation__id__in=reservation_ids) | Q(appointment__id__in=appointment_ids),
            status='COMPLETED'
        ).distinct()
        
        # Actualizar estado de la factura si es necesario
        if pagos.exists() and invoice.status != 'PAID':
            invoice.status = 'PAID'
            invoice.save()
            
        context['payments'] = pagos
        return context

class GenerateInvoiceView(RoleRequiredMixin, CreateView):
    model = Invoice
    template_name = 'invoicing/generate_invoice.html'
    fields = ['user', 'due_date', 'notes']
    success_url = reverse_lazy('invoicing:invoice_list')
    required_role = 'admin'

    def form_valid(self, form):
        # Generar número de factura único
        last_invoice = Invoice.objects.order_by('-date_created').first()
        if last_invoice:
            last_number = int(last_invoice.invoice_number.split('-')[1])
            new_number = f"INV-{str(last_number + 1).zfill(6)}"
        else:
            new_number = "INV-000001"

        form.instance.invoice_number = new_number
        form.instance.date_created = timezone.now()
        
        # Obtener todas las reservas y servicios no facturados del usuario
        user = form.instance.user
        reservations = Reservation.objects.filter(
            user=user,
            status__in=['COMPLETED', 'ACTIVE'],
            invoiceitem__isnull=True
        )
        
        carwash_services = CarWashService.objects.filter(
            user=user,
            status='COMPLETED',
            invoiceitem__isnull=True
        )

        # Calcular el total
        total_amount = 0
        if reservations.exists():
            total_amount += reservations.aggregate(Sum('total_cost'))['total_cost__sum'] or 0
        if carwash_services.exists():
            total_amount += carwash_services.aggregate(Sum('total_cost'))['total_cost__sum'] or 0

        form.instance.total_amount = total_amount
        invoice = form.save()

        # Crear items de factura para cada reserva
        for reservation in reservations:
            InvoiceItem.objects.create(
                invoice=invoice,
                description=f"Estacionamiento - {reservation.space}",
                quantity=1,
                unit_price=reservation.total_cost,
                total_price=reservation.total_cost,
                reservation=reservation
            )

        # Crear items de factura para cada servicio de lavado
        for service in carwash_services:
            InvoiceItem.objects.create(
                invoice=invoice,
                description=f"Lavado - {service.service_type}",
                quantity=1,
                unit_price=service.total_cost,
                total_price=service.total_cost,
                carwash_service=service
            )

        messages.success(self.request, 'Factura generada exitosamente.')
        return super().form_valid(form)

class UpdateInvoiceStatusView(RoleRequiredMixin, UpdateView):
    model = Invoice
    template_name = 'invoicing/update_invoice_status.html'
    fields = ['status']
    success_url = reverse_lazy('invoicing:invoice_list')
    required_role = 'admin'

    def form_valid(self, form):
        messages.success(self.request, 'Estado de la factura actualizado exitosamente.')
        return super().form_valid(form)

@require_POST
@login_required
def send_invoice_email(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    user = invoice.user or request.user
    context = {
        'invoice': invoice,
        'services': invoice.services.all() if hasattr(invoice, 'services') else [],
        'packages': invoice.packages.all() if hasattr(invoice, 'packages') else [],
    }
    html_message = render_to_string('invoicing/email/invoice.html', context)
    # === Calcular subtotal y tax dinámicamente ===
    items = invoice.items.all() if hasattr(invoice, 'items') else []
    subtotal = sum(item.total_price for item in items)
    tax = subtotal * Decimal('0.16')
    total = subtotal + tax
    # === Generar PDF en memoria ===
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    p.setFont("Helvetica-Bold", 16)
    p.drawString(72, 750, f"Factura #{invoice.invoice_number}")
    p.setFont("Helvetica", 12)
    p.drawString(72, 730, f"Cliente: {user.get_full_name() or user.username}")
    p.drawString(72, 710, f"Email: {user.email}")
    p.drawString(72, 690, f"Fecha: {invoice.date_created.strftime('%d/%m/%Y %H:%M') if invoice.date_created else ''}")
    p.drawString(72, 670, f"Método de Pago: {invoice.payment_method}")
    y = 650
    p.setFont("Helvetica-Bold", 12)
    p.drawString(72, y, "Items:")
    y -= 20
    p.setFont("Helvetica", 11)
    for item in items:
        p.drawString(80, y, f"- {item.description} x{item.quantity}  ${item.total_price}")
        y -= 18
        if y < 100:
            p.showPage()
            y = 750
    y -= 10
    p.setFont("Helvetica-Bold", 12)
    p.drawString(72, y, f"Subtotal: ${subtotal:.2f}")
    y -= 18
    p.drawString(72, y, f"IVA (16%): ${tax:.2f}")
    y -= 18
    p.drawString(72, y, f"Total: ${total:.2f}")
    p.save()
    buffer.seek(0)
    pdf_data = buffer.getvalue()
    buffer.close()
    # === Enviar correo con PDF adjunto ===
    try:
        email = EmailMessage(
            subject=f'Factura #{invoice.invoice_number} - Park & Wash',
            body='Adjunto comprobante de su factura.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )
        email.attach(f'Factura_{invoice.invoice_number}.pdf', pdf_data, 'application/pdf')
        email.content_subtype = 'html'
        email.send()
        # Notificación al admin
        admin_email = getattr(settings, 'ADMIN_EMAIL', None) or getattr(settings, 'DEFAULT_FROM_EMAIL', None)
        if admin_email:
            admin_msg = EmailMessage(
                subject=f'[ADMIN] Comprobante enviado a {user.email}',
                body=f'Se ha enviado el comprobante de la factura #{invoice.invoice_number} al usuario {user.email}.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[admin_email],
            )
            admin_msg.attach(f'Factura_{invoice.invoice_number}.pdf', pdf_data, 'application/pdf')
            admin_msg.send()
        messages.success(request, f'Comprobante enviado a {user.email} (PDF adjunto)')
    except Exception as e:
        messages.error(request, f'Error al enviar el comprobante: {str(e)}')
    return redirect('invoicing:invoice_detail', pk=invoice.id)
