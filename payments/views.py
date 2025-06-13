from django.shortcuts import render
from django.views.generic import ListView, DetailView, CreateView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from .models import Payment

# Create your views here.

class PaymentCreateView(LoginRequiredMixin, CreateView):
    model = Payment
    template_name = 'payments/payment_create.html'
    fields = ['amount', 'payment_method']
    success_url = reverse_lazy('payments:success')

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, 'Pago procesado exitosamente.')
        return super().form_valid(form)

class PaymentListView(LoginRequiredMixin, ListView):
    model = Payment
    template_name = 'payments/payment_list.html'
    context_object_name = 'payments'

    def get_queryset(self):
        return Payment.objects.filter(user=self.request.user)

class PaymentDetailView(LoginRequiredMixin, DetailView):
    model = Payment
    template_name = 'payments/payment_detail.html'
    context_object_name = 'payment'

class PaymentSuccessView(TemplateView):
    template_name = 'payments/payment_success.html'

class PaymentCancelView(TemplateView):
    template_name = 'payments/payment_cancel.html'

def stripe_webhook(request):
    # Implementación del webhook de Stripe
    pass
