from django import forms
from inventario.models import Sucursal

class LoginForm(forms.Form):
    usuario = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Usuario'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Contraseña'}))
    sucursal = forms.ModelChoiceField(
        queryset=Sucursal.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label="Seleccionar sucursal...",
        required=True
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Recarga dinámicamente las sucursales
        self.fields['sucursal'].queryset = Sucursal.objects.all()