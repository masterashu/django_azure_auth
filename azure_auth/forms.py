from django import forms


class UserCreateForm(forms.Form):
    username = forms.CharField(max_length=40, required=True, strip=True)
    first_name = forms.CharField(max_length=64, required=True)
    last_name = forms.CharField(max_length=64, required=True)
    password = forms.CharField(widget=forms.PasswordInput,
                               min_length=10,
                               required=True,
                               )
    job_title = forms.CharField(max_length=64)


class UserUpdateForm(forms.Form):
    username = forms.CharField(max_length=40, required=True, strip=True)
    first_name = forms.CharField(max_length=64, required=True)
    last_name = forms.CharField(max_length=64, required=True)
    job_title = forms.CharField(max_length=64, required=False)

