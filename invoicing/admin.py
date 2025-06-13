from django.contrib import admin
from .models import ServiceCategory, Service, Package, Invoice, InvoiceItem
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from django.http import HttpResponse
import os
import stat
import datetime

@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'icon')
    search_fields = ('name',)

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'estimated_time', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('name', 'description')
    list_editable = ('price', 'is_active')

@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = ('name', 'discount_percentage', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    filter_horizontal = ('services',)
    list_editable = ('discount_percentage', 'is_active')

class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 0
    readonly_fields = ['total_price']

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'user', 'date_created', 'due_date', 'total_amount', 'status']
    list_filter = ['status', 'date_created', 'due_date']
    search_fields = ['invoice_number', 'user__username', 'user__email']
    readonly_fields = ['invoice_number', 'date_created', 'total_amount']
    inlines = [InvoiceItemInline]
    date_hierarchy = 'date_created'
    actions = ['generate_ticket']

    def save_model(self, request, obj, form, change):
        if not change:  # Si es una nueva factura
            # Generar número de factura único
            last_invoice = Invoice.objects.order_by('-date_created').first()
            if last_invoice:
                last_number = int(last_invoice.invoice_number.split('-')[1])
                new_number = f"INV-{str(last_number + 1).zfill(6)}"
            else:
                new_number = "INV-000001"
            obj.invoice_number = new_number
        super().save_model(request, obj, form, change)

    def generate_ticket(self, request, queryset):
        for invoice in queryset:
            ticket_dir = os.path.join('media', 'tickets')
            if not os.path.exists(ticket_dir):
                os.makedirs(ticket_dir, exist_ok=True)
            else:
                os.chmod(ticket_dir, stat.S_IWRITE | stat.S_IREAD | stat.S_IWUSR | stat.S_IRUSR | stat.S_IWGRP | stat.S_IRGRP | stat.S_IWOTH | stat.S_IROTH)
            timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
            filename = f"ticket_{invoice.invoice_number}_{timestamp}.pdf"
            filepath = os.path.join(ticket_dir, filename)
            doc = SimpleDocTemplate(filepath, pagesize=letter)
            styles = getSampleStyleSheet()
            style_center = ParagraphStyle(name='Center', parent=styles['Normal'], alignment=TA_CENTER, fontSize=14, spaceAfter=8)
            style_left = ParagraphStyle(name='Left', parent=styles['Normal'], alignment=TA_LEFT, fontSize=12)
            elements = []

            # Encabezado
            elements.append(Paragraph('<b>ISFAJ</b>', style_center))
            elements.append(Paragraph('Autolavado y Estacionamiento', style_center))
            elements.append(Paragraph('C. Benito Juárez 13, 50640 Ejido de San Juan Jalpa, Méx.', style_center))
            elements.append(Paragraph('Tel: (55) 1234-5678 | Email: contacto@isfaj.com', style_center))
            elements.append(Spacer(1, 10))
            elements.append(Paragraph(f'<b>Ticket de Factura: {invoice.invoice_number}</b>', style_center))
            elements.append(Paragraph(f'Fecha de Emisión: {invoice.date_created.strftime("%Y-%m-%d %H:%M %Z")}', style_center))
            elements.append(Spacer(1, 20))

            # Información del Cliente
            elements.append(Paragraph('<b>Información del Cliente</b>', style_left))
            elements.append(Spacer(1, 4))
            data_cliente = [
                ['<b>Cliente:</b>', invoice.user.username if invoice.user else ''],
                ['<b>Fecha de Servicio:</b>', invoice.date_created.strftime('%Y-%m-%d %H:%M')],
                ['<b>Método de Pago:</b>', invoice.get_payment_method_display() if hasattr(invoice, 'get_payment_method_display') else (invoice.payment_method or '')],
            ]
            table_cliente = Table(data_cliente, colWidths=[120, 300])
            table_cliente.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('LINEBELOW', (0, 1), (-1, 1), 0.5, colors.black),
            ]))
            elements.append(table_cliente)
            elements.append(Spacer(1, 18))

            # Detalles del Servicio
            elements.append(Paragraph('<b>Detalles del Servicio</b>', style_left))
            elements.append(Spacer(1, 4))
            data_servicio = [['Descripción', 'Cantidad', 'Costo']]
            for item in invoice.items.all():
                data_servicio.append([
                    item.description,
                    str(item.quantity),
                    f"${item.total_price:,.2f}"
                ])
            data_servicio.append(['', '<b>Total:</b>', f"<b>${invoice.total_amount:,.2f}</b>"])
            table_servicio = Table(data_servicio, colWidths=[260, 80, 80])
            table_servicio.setStyle(TableStyle([
                ('GRID', (0, 0), (-1, -2), 1, colors.black),
                ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                ('TOPPADDING', (0, 0), (-1, 0), 6),
                ('ALIGN', (2, 1), (2, -1), 'RIGHT'),
                ('SPAN', (0, -1), (1, -1)),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ]))
            elements.append(table_servicio)
            elements.append(Spacer(1, 18))

            # Mensaje final
            elements.append(Paragraph('<i>Gracias por elegir ISFAJ. Su confianza nos impulsa a seguir mejorando.</i>', style_center))
            elements.append(Paragraph('<b>Sistema desarrollado por TEAMDEVB.</b>', style_center))
            elements.append(Paragraph('Para cualquier consulta, contáctenos en contacto@isfaj.com.', style_center))

            doc.build(elements)
            # Cambiar estado a 'PAID' y guardar
            invoice.status = 'PAID'
            invoice.save()
            self.message_user(request, f"Ticket generado para factura {invoice.invoice_number} en {filepath}")
    generate_ticket.short_description = "Generar Ticket"
