from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile, UserPreference, UserVehicle

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    maternal_lastname = forms.CharField(max_length=30, required=False)
    phone_number = forms.CharField(max_length=15, required=False)
    car_brand = forms.CharField(max_length=50, required=False)
    car_model = forms.CharField(max_length=50, required=False)
    license_plate = forms.CharField(max_length=10, required=False)
    car_photo = forms.ImageField(required=False)

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
            # Create or update the user profile
            UserProfile.objects.update_or_create(
                user=user,
                defaults={
                    'phone_number': self.cleaned_data.get('phone_number'),
                    'car_brand': self.cleaned_data.get('car_brand'),
                    'car_model': self.cleaned_data.get('car_model'),
                    'license_plate': self.cleaned_data.get('license_plate'),
                    'car_photo': self.cleaned_data.get('car_photo'),
                }
            )
        return user

class UserPreferenceForm(forms.ModelForm):
    class Meta:
        model = UserPreference
        fields = ['preferred_parking_locations', 'notification_preferences', 'theme_preference']
        widgets = {
            'preferred_parking_locations': forms.CheckboxSelectMultiple(),
            'notification_preferences': forms.CheckboxSelectMultiple(),
            'theme_preference': forms.RadioSelect(),
        }

class UserVehicleForm(forms.ModelForm):
    class Meta:
        model = UserVehicle
        fields = ['plate_number', 'brand', 'model', 'color', 'is_favorite']
        widgets = {
            'plate_number': forms.TextInput(attrs={'class': 'form-control'}),
            'brand': forms.TextInput(attrs={'class': 'form-control'}),
            'model': forms.TextInput(attrs={'class': 'form-control'}),
            'color': forms.TextInput(attrs={'class': 'form-control'}),
            'is_favorite': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_plate_number(self):
        plate_number = self.cleaned_data['plate_number']
        # Validar formato de placa (ejemplo para formato mexicano)
        if not plate_number.replace('-', '').isalnum():
            raise forms.ValidationError('La placa debe contener solo letras y números.')
        return plate_number 