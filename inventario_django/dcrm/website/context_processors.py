def user_rol(request):
    """
    Inyecta la variable 'user_rol' en todos los templates.
    Valores posibles: 'ADMIN', 'ORGANIZADOR', 'RESIDENTE', None (no autenticado).
    """
    if not request.user.is_authenticated:
        return {'user_rol': None}

    u = request.user

    if u.is_superuser or u.groups.filter(name='ADMIN').exists():
        return {'user_rol': 'ADMIN'}

    if u.groups.filter(name='ORGANIZADOR').exists():
        return {'user_rol': 'ORGANIZADOR'}

    return {'user_rol': 'RESIDENTE'}
