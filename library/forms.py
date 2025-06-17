from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Q
from .models import (
    CustomUser, Genre, Author, Book, BookPurchase,
    Payment, Deposit, Delivery
)


class BookSearchForm(forms.Form):
    """Formulaire de recherche de livres"""
    query = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Rechercher par titre, auteur, ISBN...'
        }),
        label='Recherche'
    )
    
    genre = forms.ModelChoiceField(
        queryset=Genre.objects.all(),
        required=False,
        empty_label="Tous les genres",
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Genre'
    )
    
    author = forms.ModelChoiceField(
        queryset=Author.objects.all(),
        required=False,
        empty_label="Tous les auteurs",
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Auteur'
    )
    
    language = forms.ChoiceField(
        choices=[('', 'Toutes les langues')] + Book.LANGUAGES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Langue'
    )
    
    available_only = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='Disponibles uniquement'
    )


class UserRegistrationForm(UserCreationForm):
    """Formulaire d'inscription utilisateur"""
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
        label='Adresse email'
    )
    
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label='Prénom'
    )
    
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label='Nom'
    )
    
    phone_number = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label='Numéro de téléphone'
    )
    
    address = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        label='Adresse'
    )
    
    date_of_birth = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label='Date de naissance'
    )
    
    category = forms.ChoiceField(
        choices=CustomUser.USER_CATEGORIES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Catégorie'
    )
    
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'first_name', 'last_name', 'phone_number', 
                 'address', 'date_of_birth', 'category', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control'})
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.phone_number = self.cleaned_data['phone_number']
        user.address = self.cleaned_data['address']
        user.date_of_birth = self.cleaned_data['date_of_birth']
        user.category = self.cleaned_data['category']
        
        if commit:
            user.save()
        return user


class LoanForm(forms.Form):
    """Formulaire pour créer un emprunt"""
    user = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(is_active_member=True),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Utilisateur'
    )
    
    book = forms.ModelChoiceField(
        queryset=Book.objects.filter(available_copies__gt=0),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Livre'
    )
    
    due_date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label='Date de retour prévue'
    )
    
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        label='Notes'
    )




class BookCoverUploadForm(forms.ModelForm):
    """Formulaire pour télécharger une image de couverture"""

    class Meta:
        model = Book
        fields = ['cover_image']
        widgets = {
            'cover_image': forms.FileInput(attrs={
                'class': 'form-control drag-drop-input',
                'accept': 'image/*',
                'data-max-size': '5242880',  # 5MB en bytes
                'data-allowed-types': 'image/jpeg,image/png,image/gif,image/webp'
            })
        }
        labels = {
            'cover_image': 'Image de couverture'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cover_image'].help_text = 'Formats acceptés: JPG, PNG, GIF, WebP. Taille max: 5MB. Dimensions recommandées: 400x600 pixels.'

    def clean_cover_image(self):
        image = self.cleaned_data.get('cover_image')
        if image:
            # Vérifier la taille du fichier (5MB max)
            if image.size > 5 * 1024 * 1024:
                raise forms.ValidationError("L'image ne doit pas dépasser 5MB.")

            # Vérifier le type de fichier
            allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
            if image.content_type not in allowed_types:
                raise forms.ValidationError("Format d'image non supporté. Utilisez JPG, PNG, GIF ou WebP.")

            # Vérifier les dimensions (optionnel)
            try:
                from PIL import Image
                img = Image.open(image)
                width, height = img.size

                # Recommandations pour les dimensions
                if width < 200 or height < 300:
                    raise forms.ValidationError("L'image est trop petite. Dimensions minimales: 200x300 pixels.")

                if width > 2000 or height > 3000:
                    raise forms.ValidationError("L'image est trop grande. Dimensions maximales: 2000x3000 pixels.")

            except ImportError:
                # PIL n'est pas installé, on passe la validation des dimensions
                pass
            except Exception:
                raise forms.ValidationError("Impossible de traiter l'image. Vérifiez que le fichier n'est pas corrompu.")

        return image


class BookPurchaseForm(forms.ModelForm):
    """Formulaire pour l'achat de livres"""

    class Meta:
        model = BookPurchase
        fields = ['quantity', 'delivery_preference', 'delivery_address', 'recipient_name', 'recipient_phone', 'delivery_instructions', 'notes']
        widgets = {
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '10'}),
            'delivery_preference': forms.Select(attrs={'class': 'form-control'}),
            'delivery_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'recipient_name': forms.TextInput(attrs={'class': 'form-control'}),
            'recipient_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'delivery_instructions': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
        labels = {
            'quantity': 'Quantité',
            'delivery_preference': 'Mode de livraison',
            'delivery_address': 'Adresse de livraison',
            'recipient_name': 'Nom du destinataire',
            'recipient_phone': 'Téléphone du destinataire',
            'delivery_instructions': 'Instructions de livraison',
            'notes': 'Notes (optionnel)'
        }

    def __init__(self, *args, **kwargs):
        self.book = kwargs.pop('book', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if self.book:
            self.fields['quantity'].help_text = f'Prix unitaire: {self.book.purchase_price}€'

        # Pré-remplir les informations utilisateur
        if self.user:
            self.fields['recipient_name'].initial = self.user.get_full_name() or self.user.username
            if hasattr(self.user, 'phone'):
                self.fields['recipient_phone'].initial = self.user.phone

        # Rendre certains champs optionnels
        self.fields['recipient_name'].required = False
        self.fields['recipient_phone'].required = False
        self.fields['delivery_instructions'].required = False
        self.fields['notes'].required = False

    def clean_quantity(self):
        quantity = self.cleaned_data['quantity']
        if quantity < 1:
            raise forms.ValidationError("La quantité doit être d'au moins 1.")
        if quantity > 10:
            raise forms.ValidationError("La quantité ne peut pas dépasser 10.")
        return quantity

    def clean(self):
        cleaned_data = super().clean()
        delivery_preference = cleaned_data.get('delivery_preference')
        delivery_address = cleaned_data.get('delivery_address')

        # Vérifier que l'adresse est fournie pour les livraisons à domicile
        if delivery_preference in ['home_delivery', 'express'] and not delivery_address:
            raise forms.ValidationError("L'adresse de livraison est requise pour la livraison à domicile.")

        return cleaned_data


class PaymentForm(forms.ModelForm):
    """Formulaire pour enregistrer un paiement"""

    class Meta:
        model = Payment
        fields = ['payment_method', 'transaction_id', 'notes']
        widgets = {
            'payment_method': forms.Select(attrs={'class': 'form-control'}),
            'transaction_id': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'payment_method': 'Méthode de paiement',
            'transaction_id': 'ID de transaction (optionnel)',
            'notes': 'Notes (optionnel)'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['transaction_id'].required = False
        self.fields['notes'].required = False


class DepositForm(forms.ModelForm):
    """Formulaire pour les cautions"""

    class Meta:
        model = Deposit
        fields = ['amount', 'reason']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'amount': 'Montant de la caution (€)',
            'reason': 'Raison'
        }

    def clean_amount(self):
        amount = self.cleaned_data['amount']
        if amount <= 0:
            raise forms.ValidationError("Le montant doit être positif.")
        return amount




class QuickLoanForm(forms.Form):
    """Formulaire rapide pour créer un emprunt"""
    user = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(is_active_member=True),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Utilisateur'
    )

    book = forms.ModelChoiceField(
        queryset=Book.objects.filter(available_copies__gt=0),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Livre'
    )

    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        label='Notes (optionnel)'
    )

    def clean(self):
        cleaned_data = super().clean()
        user = cleaned_data.get('user')
        book = cleaned_data.get('book')

        if user and book:
            # Vérifier si l'utilisateur peut emprunter plus de livres
            if not user.can_borrow_more:
                raise forms.ValidationError(f"L'utilisateur a atteint sa limite d'emprunts.")

            # Vérifier si le livre est disponible
            if not book.is_available:
                raise forms.ValidationError("Ce livre n'est pas disponible.")

            # Plus de vérification de conditions spéciales

        return cleaned_data


class SuperAdminPromotionForm(forms.Form):
    """Formulaire pour promouvoir un utilisateur en super admin"""
    user = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(is_active=True),
        label="Utilisateur",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    admin_type = forms.ChoiceField(
        choices=[
            ('staff', 'Staff (Bibliothécaire)'),
            ('super_admin', 'Super Admin'),
            ('regular', 'Utilisateur régulier')
        ],
        label="Type d'administrateur",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    confirm = forms.BooleanField(
        required=True,
        label="Je confirme cette modification de privilèges",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    def __init__(self, *args, **kwargs):
        self.current_user = kwargs.pop('current_user', None)
        super().__init__(*args, **kwargs)

        # Exclure l'utilisateur actuel et les superusers de la liste
        if self.current_user:
            self.fields['user'].queryset = CustomUser.objects.filter(
                is_active=True
            ).exclude(
                Q(id=self.current_user.id) | Q(is_superuser=True)
            )

    def clean(self):
        cleaned_data = super().clean()
        user = cleaned_data.get('user')
        admin_type = cleaned_data.get('admin_type')

        if user and admin_type:
            # Vérifier que l'utilisateur actuel a les droits pour cette action
            if self.current_user and not self.current_user.can_manage_users:
                raise forms.ValidationError(
                    "Vous n'avez pas les droits nécessaires pour modifier les privilèges administratifs."
                )

            # Vérifier que l'utilisateur n'est pas déjà du type demandé
            if admin_type == 'staff' and user.is_staff and not user.is_super_admin:
                raise forms.ValidationError(
                    f"{user.get_full_name()} est déjà membre du staff."
                )
            elif admin_type == 'super_admin' and user.is_super_admin:
                raise forms.ValidationError(
                    f"{user.get_full_name()} est déjà super administrateur."
                )
            elif admin_type == 'regular' and not user.is_staff and not user.is_super_admin:
                raise forms.ValidationError(
                    f"{user.get_full_name()} est déjà un utilisateur régulier."
                )

        return cleaned_data


class DeliveryForm(forms.ModelForm):
    """Formulaire pour créer/modifier une livraison"""

    class Meta:
        model = Delivery
        fields = [
            'delivery_method', 'delivery_address', 'pickup_location',
            'estimated_delivery_date', 'recipient_name', 'recipient_phone',
            'recipient_email', 'delivery_instructions', 'delivery_cost'
        ]
        widgets = {
            'delivery_method': forms.Select(attrs={'class': 'form-control'}),
            'delivery_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'pickup_location': forms.TextInput(attrs={'class': 'form-control'}),
            'estimated_delivery_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'recipient_name': forms.TextInput(attrs={'class': 'form-control'}),
            'recipient_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'recipient_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'delivery_instructions': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'delivery_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }
        labels = {
            'delivery_method': 'Méthode de livraison',
            'delivery_address': 'Adresse de livraison',
            'pickup_location': 'Lieu de retrait',
            'estimated_delivery_date': 'Date de livraison estimée',
            'recipient_name': 'Nom du destinataire',
            'recipient_phone': 'Téléphone',
            'recipient_email': 'Email',
            'delivery_instructions': 'Instructions de livraison',
            'delivery_cost': 'Coût de livraison (€)',
        }

    def __init__(self, *args, **kwargs):
        self.purchase = kwargs.pop('purchase', None)
        super().__init__(*args, **kwargs)

        # Pré-remplir avec les données de l'achat si disponible
        if self.purchase:
            self.fields['delivery_address'].initial = self.purchase.delivery_address
            self.fields['recipient_name'].initial = self.purchase.user.get_full_name() or self.purchase.user.username
            self.fields['recipient_email'].initial = self.purchase.user.email

        # Rendre certains champs conditionnels
        self.fields['pickup_location'].required = False
        self.fields['recipient_phone'].required = False
        self.fields['delivery_instructions'].required = False

    def clean(self):
        cleaned_data = super().clean()
        delivery_method = cleaned_data.get('delivery_method')
        delivery_address = cleaned_data.get('delivery_address')
        pickup_location = cleaned_data.get('pickup_location')

        # Validation selon la méthode de livraison
        if delivery_method == 'pickup':
            if not pickup_location:
                raise forms.ValidationError("Le lieu de retrait est requis pour le retrait en bibliothèque.")
        elif delivery_method in ['home_delivery', 'express', 'registered']:
            if not delivery_address:
                raise forms.ValidationError("L'adresse de livraison est requise pour la livraison à domicile.")

        return cleaned_data


class DeliveryTrackingForm(forms.ModelForm):
    """Formulaire pour mettre à jour le suivi de livraison"""

    class Meta:
        model = Delivery
        fields = ['status', 'tracking_number', 'carrier', 'notes']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}),
            'tracking_number': forms.TextInput(attrs={'class': 'form-control'}),
            'carrier': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'status': 'Statut de livraison',
            'tracking_number': 'Numéro de suivi',
            'carrier': 'Transporteur',
            'notes': 'Notes',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tracking_number'].required = False
        self.fields['carrier'].required = False
        self.fields['notes'].required = False
