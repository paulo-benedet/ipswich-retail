from django import forms


class AddToBasketForm(forms.Form):
    quantity = forms.IntegerField(min_value=1, max_value=2147483647)
