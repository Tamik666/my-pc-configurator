from decimal import Decimal

from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .models import Build, Component


def catalog(request):
    selected_ids = [str(value) for value in request.session.get("build", [])]

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "clear":
            request.session["build"] = []
            return redirect("catalog")
            
        if action == "save":
            components = Component.objects.filter(pk__in=selected_ids)
            if components.exists():
                build = Build.objects.create(
                    name=request.POST.get("name", "").strip() or "Моя сборка"
                )
                build.components.set(components)
                return redirect("build_detail", share_id=build.share_id)
            return redirect("catalog")
        component_id = request.POST.get("component_id")

        if action == "add":
            component = get_object_or_404(
                Component,
                pk=component_id,
                in_stock=True,
            )
            
            selected_ids = [
                str(item.pk)
                for item in Component.objects.filter(pk__in=selected_ids)
                if item.category != component.category
            ]
            selected_ids.append(str(component.pk))

        elif action == "remove":
            selected_ids = [
                value for value in selected_ids
                if value != str(component_id)
            ]
        request.session["build"] = selected_ids
        return redirect("catalog")

    query = request.GET.get("q", "").strip()
    selected_category = request.GET.get("category", "")
    categories = Component.Category.choices
    category_values = [value for value, _label in categories]

    components = Component.objects.filter(in_stock=True)
    if query:
        components = components.filter(Q(name__icontains=query))
    if selected_category in category_values:
        components = components.filter(category=selected_category)
    else:
        selected_category = ""

    selected_components = Component.objects.filter(pk__in=selected_ids)
    progress = get_build_details(selected_components)
    completed_count = sum(item["selected"] for item in progress)
    warnings = compatibility_warnings(selected_components)

    total = sum(
        (component.price for component in selected_components),
        Decimal(0),
    )
    return render(request, "builder/catalog.html", {
        "components": components,
        "categories": categories,
        "query": query,
        "selected_category": selected_category,
        "selected_components": selected_components,
        "compatibility_warnings": warnings,
        "build_progress": progress,
        "completed_count": completed_count,
        "category_count": len(progress),
        "total": total
    })

def build_detail(request, share_id):
    build = get_object_or_404(
        Build.objects.prefetch_related("components"),
        share_id=share_id,
    )
    components = build.components.all()
    warnings = compatibility_warnings(components)
    total = sum(
        (component.price for component in components),
        Decimal(0)
    )

    return render(request, "builder/build_detail.html", {
        "build": build,
        "components": components,
        "compatibility_warnings": warnings,
        "total": total,
    })

def compatibility_warnings(components):
    by_category = {component.category: component for component in components}

    processor = by_category.get(Component.Category.PROCESSOR)
    motherboard = by_category.get(Component.Category.MOTHERBOARD)
    memory = by_category.get(Component.Category.MEMORY)

    def spec(component, key):
        if not component or not isinstance(component.specifications, dict):
            return ""
        return str(component.specifications.get(key, "")).strip()

    warnings = []

    cpu_socket = spec(processor, "socket")
    board_socket = spec(motherboard, "socket")
    if cpu_socket and board_socket and cpu_socket != board_socket:
        warnings.append(
            f"Сокет процессора ({cpu_socket}) не совпадает с сокетом платы ({board_socket})"
        )

    memory_type = spec(memory, "memory_type")
    board_memory_type = spec(motherboard, "memory_type")
    if memory_type and board_memory_type and memory_type != board_memory_type:
        warnings.append(
            f"Тип памяти ({memory_type}) не совпадает с сокетом платы ({board_memory_type})"
        )
    return warnings

def get_build_details(components):
    selected_categories = {
        component.category for component in components
    }

    return [
        {
            "label": label,
            "selected":value in selected_categories
        }
        for value, label in Component.Category.choices
    ]