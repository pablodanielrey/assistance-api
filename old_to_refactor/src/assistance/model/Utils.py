from users.model.entities.User import IdentityNumberTypes

def map_user_from_model(user):
    """
        mapea los datos de un usuario del modelo actual hacia el viejo usado por tutorias.
    """
    u = {
        'id': user.id,
        'nombre': user.firstname,
        'apellido': user.lastname,
        'dni': '',
        'legajo': ''
    }

    dnis = [d for d in user.identity_numbers if not d.deleted and d.type == IdentityNumberTypes.DNI]
    if len(dnis) > 0:
        u['dni'] = dnis[0].number

    legajos = [d for d in user.identity_numbers if not d.deleted and d.type == IdentityNumberTypes.STUDENT]
    if len(legajos) > 0:
        u['legajo'] = legajos[0].number


    return u


def map_place_from_model(place):
    p = {
        'id': place.id,
        'nombre': place.name,
        'padre_id': place.parent_id
    }
    return p