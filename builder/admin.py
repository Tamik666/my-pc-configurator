from django import forms
from django.contrib import admin

from .models import Component

SOCKET_CHOICES = [
    ("", "---------"),
    ("AM4", "AM4"),
    ("AM5", "AM5"),
    ("LGA1200", "LGA1200"),
    ("LGA1700", "LGA1700"),
    ("LGA1851", "LGA1851"),
]
MEMORY_CHOICES = [("", "---------"), ("DDR4", "DDR4"), ("DDR5", "DDR5")]
FORM_FACTOR_CHOICES = [
    ("ATX", "ATX"),
    ("mATX", "mATX"),
    ("Mini-ITX", "Mini-ITX"),
    ("E-ATX", "E-ATX"),
]
INTERFACE_CHOICES = [
    ("", "---------"),
    ("NVMe", "NVMe"),
    ("SATA", "SATA"),
    ("PCIe", "PCIe"),
]


class ComponentAdminForm(forms.ModelForm):
    socket = forms.ChoiceField(label="Сокет", required=False, choices=SOCKET_CHOICES)
    memory_type = forms.ChoiceField(label="Тип памяти", required=False, choices=MEMORY_CHOICES)
    capacity_gb = forms.ChoiceField(
        label="Объём памяти, ГБ",
        required=False,
        choices=[("", "---------")] + [(str(size), f"{size} ГБ") for size in (8, 10, 12, 16, 24, 32, 48, 64, 96, 128)],
    )
    interface = forms.ChoiceField(label="Интерфейс", required=False, choices=INTERFACE_CHOICES)
    form_factor = forms.ChoiceField(
        label="Формат платы", required=False, choices=[("", "---------")] + FORM_FACTOR_CHOICES
    )
    supported_form_factors = forms.MultipleChoiceField(
        label="Форматы, поддерживаемые корпусом",
        required=False,
        choices=FORM_FACTOR_CHOICES,
        help_text="Можно выбрать несколько форматов, удерживая Cmd или Ctrl.",
    )
    tdp_w = forms.IntegerField(label="TDP, Вт", required=False, min_value=0)
    length_mm = forms.IntegerField(label="Длина видеокарты, мм", required=False, min_value=0)
    max_gpu_length_mm = forms.IntegerField(label="Максимальная длина видеокарты, мм", required=False, min_value=0)
    wattage_w = forms.IntegerField(label="Мощность блока питания, Вт", required=False, min_value=0)
    radiator_mm = forms.IntegerField(label="Размер радиатора, мм", required=False, min_value=0)

    class Meta:
        model = Component
        fields = ("category", "name", "price", "in_stock")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        specs = self.instance.specifications if isinstance(self.instance.specifications, dict) else {}
        for key in ("socket", "memory_type", "capacity_gb", "interface", "form_factor"):
            value = specs.get(key)
            if value not in (None, ""):
                self.initial[key] = str(value)
                choices = list(self.fields[key].choices)
                if str(value) not in {choice[0] for choice in choices}:
                    self.fields[key].choices = choices + [(str(value), str(value))]

        supported = specs.get("supported_form_factors", [])
        if isinstance(supported, str):
            supported = [supported]
        self.initial["supported_form_factors"] = [str(value) for value in supported]
        for value in supported:
            if value not in {choice[0] for choice in self.fields["supported_form_factors"].choices}:
                self.fields["supported_form_factors"].choices = list(self.fields["supported_form_factors"].choices) + [
                    (str(value), str(value))
                ]

        for key in ("tdp_w", "length_mm", "max_gpu_length_mm", "wattage_w", "radiator_mm"):
            if specs.get(key) not in (None, ""):
                self.initial[key] = specs[key]

    def save(self, commit=True):
        component = super().save(commit=False)
        specs = dict(component.specifications) if isinstance(component.specifications, dict) else {}
        field_keys = (
            "socket", "memory_type", "capacity_gb", "interface", "form_factor",
            "supported_form_factors", "tdp_w", "length_mm", "max_gpu_length_mm", "wattage_w", "radiator_mm",
        )
        for key in field_keys:
            value = self.cleaned_data.get(key)
            if value in (None, "", []):
                specs.pop(key, None)
            elif key in {"tdp_w", "length_mm", "max_gpu_length_mm", "wattage_w", "radiator_mm", "capacity_gb"}:
                specs[key] = int(value)
            elif key == "supported_form_factors":
                specs[key] = list(value)
            else:
                specs[key] = value

        component.specifications = specs
        if commit:
            component.save()
        return component


@admin.register(Component)
class ComponentAdmin(admin.ModelAdmin):
    form = ComponentAdminForm
    list_display = ("name", "category", "price", "in_stock")
    list_filter = ("category", "in_stock",)
    search_fields = ("name",)
    ordering = ("category", "name")
    fieldsets = (
        ("Комплектующая", {"fields": ("category", "name", "price", "in_stock")}),
        ("Основные характеристики", {"fields": ("socket", "memory_type", "capacity_gb", "interface", "form_factor", "supported_form_factors"), "classes": ("collapse",)}),
        ("Размеры и мощность", {"fields": ("tdp_w", "length_mm", "max_gpu_length_mm", "wattage_w", "radiator_mm"), "classes": ("collapse",)}),
    )
