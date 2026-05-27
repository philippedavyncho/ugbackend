from .models import TypeVitre


def list_types_vitres():
    return TypeVitre.objects.all()
