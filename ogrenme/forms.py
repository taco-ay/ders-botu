# ogrenme/forms.py

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

# Django'nun varsayılan UserCreationForm'unu kullanıyoruz.
# Eğer daha sonra ekstra alanlar eklemek isterseniz, bu sınıfı genişletebilirsiniz.
class KayitFormu(UserCreationForm):
    class Meta:
        model = User
        # Kullanıcı adı ve şifre alanlarını kullanacağız
        fields = ("username",)