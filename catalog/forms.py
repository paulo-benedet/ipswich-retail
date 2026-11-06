from django import forms


class AddToBasketForm(forms.Form):
    quantity = forms.IntegerField(min_value=1, max_value=2147483647)


class DeliveryDetailsForm(forms.Form):
    first_name = forms.CharField(label="First name", max_length=100)
    last_name = forms.CharField(label="Last name", max_length=100)
    email = forms.EmailField(label="Email address", max_length=254)
    address_line1 = forms.CharField(label="Address line 1", max_length=200)
    address_line2 = forms.CharField(label="Address line 2 (optional)", max_length=200, required=False)
    city = forms.CharField(label="Town or city", max_length=100)
    postcode = forms.RegexField(
        label="Postcode", max_length=10,
        regex=r"(?i)^(?:GIR ?0AA|[A-Z]{1,2}[0-9][A-Z0-9]? ?[0-9][A-Z]{2})$",
        error_messages={"invalid": "Enter a valid UK postcode, for example IP1 1AA."},
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        autocomplete = ["given-name", "family-name", "email", "address-line1", "address-line2", "address-level2", "postal-code"]
        for (name, field), hint in zip(self.fields.items(), autocomplete):
            field.widget.attrs["autocomplete"] = hint
            field.error_messages["required"] = f"Enter your {field.label.lower()}."
            if self.is_bound and name in self.errors:
                field.widget.attrs.update({"aria-invalid": "true", "aria-describedby": f"id_{name}_errors"})

    def clean_postcode(self):
        value = self.cleaned_data["postcode"].replace(" ", "").upper()
        return value[:-3] + " " + value[-3:]
