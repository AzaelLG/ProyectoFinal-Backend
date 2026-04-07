import json
import uuid
import bcrypt
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from api.models import User, UserCharacterSelected, Character, Run

@csrf_exempt
def register_user(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method must be POST'}, status=401)
    try:
        body_json = json.loads(request.body)
    except json.decoder.JSONDecodeError:
        return JsonResponse({'error':'Json inválido'},status = 400)

    username = body_json['username']
    password = body_json['password']
    cpassword = body_json['cpassword']

    #Comprobación de datos
    if not username or not password or not cpassword:
        return JsonResponse({'error':'Falta usuario, contraseña o confirmar contraseña'},status = 400)
    if password != cpassword:
        return JsonResponse({'error':'Las contraseñas no coinciden'},status = 400)
    if User.objects.filter(username=username).exists():
        return JsonResponse({'error':'Usuario ya existente'},status = 400)

    #Encriptación contraseña
    encrypt = bcrypt.gensalt()
    hased_password = bcrypt.hashpw(password.encode('utf8'), encrypt).decode('utf8')

    #Creación usuario
    new_user =User(username=username, password=hased_password)
    new_user.save()
    return JsonResponse({'status': 'Usuario creado correctamente'},status = 200)

def get_user(request):
    if request.method != 'GET':
        return JsonResponse({'error': 'Method must be GET'}, status=401)
    session_token = request.headers.get('session')

    #Comprobaciones de datos
    if not session_token:
        return JsonResponse({'error': 'Session token no valido'}, status=401)
    try:
        user = User.objects.get(session_token=session_token)
    except User.DoesNotExist:
        return JsonResponse({'error': 'Session token no valido'}, status=401)
    try:
        favorito = UserCharacterSelected.objects.get(user=user, is_selected = True)
    except UserCharacterSelected.DoesNotExist:
    #Si no tiene favorito se le asigna el default
        try:
            personaje_base = Character.objects.get(id=1)
            favorito = UserCharacterSelected.objects.create(
                user=user,
                character = personaje_base,
                is_selected = True
            )
        except Character.DoesNotExist:
            return JsonResponse({'error': 'Personaje no existe'}, status=404)
    return JsonResponse({
            'username': user.username,
            'special_money' : user.special_money,
            'volume' : user.volume,
            'resolution' : user.resolution,
            'is_selected' : favorito.character.name
        })

@csrf_exempt
def favorite(request, character_id):
    if request.method != 'PUT':
        return JsonResponse({'error': 'Método inválido'}, status=401)

    #Comprobación de datos
    session_token = request.headers.get('Authorization')
    character_id = request.headers.get('id')

    if not session_token or not session_token.startswith('Bearer '):
        return JsonResponse({'error': 'Session token no proporcionado'}, status=401)

    session_token = session_token.split(' ')[1]
    try:
        user = User.objects.get(session_token=session_token)
    except User.DoesNotExist:
        return JsonResponse({'error': 'Session token no valido'}, status=400)

    try:
        personaje_nuevo = Character.objects.get(id=character_id)
    except Character.DoesNotExist:
        return JsonResponse({'error': 'Personaje no existe'}, status=404)
    try:
        relacion_inventario = UserCharacterSelected.objects.get(user=user, character = personaje_nuevo)
    except UserCharacterSelected.DoesNotExist:
        return JsonResponse({'error': 'Personaje no existe'}, status=404)

    #Cambio de favorito
    UserCharacterSelected.objects.filter(user=user,is_selected = True).update(is_selected = False)
    relacion_inventario.is_selected = True
    relacion_inventario.save()
    return JsonResponse({'status':'Personaje favorito actualizado'}, status=200)

@csrf_exempt
def login(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Método inválido'}, status=401)
    try:
        body_json = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)

    username = body_json.get('username')
    password = body_json.get('password')
    #Validar datos
    if not username or not password:
        return JsonResponse({'error': 'Falta username o password'}, status=401)

    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return JsonResponse({'error': 'Credenciales incorrectas'}, status=401)

    #Validar contraseña con Bcrypt
    if not bcrypt.checkpw(password.encode('utf8'), user.password.encode('utf8')):
        return JsonResponse({'error': 'Credenciales incorrectas'}, status=401)

    #Generar sesión y guardarla
    new_session_token = str(uuid.uuid4())
    user.session_token = new_session_token
    user.save()

    return JsonResponse({"session": new_session_token}, status=201)

def get_characters(request):
    if request.method != 'GET':
        return JsonResponse({'error': 'Método invalido'}, status=401)

    #Validar datos
    auth_header = request.headers.get('Authorization')

    if not auth_header or not auth_header.startswith('Bearer '):
        return JsonResponse({'error': 'Session token no proporcionado'}, status=401)


    session_token = auth_header.split(' ')[1]

    try:
        user = User.objects.get(session_token=session_token)
    except User.DoesNotExist:
        return JsonResponse({'error': 'Session token no valido'}, status=400)

    personajes = Character.objects.all()

    inventario = UserCharacterSelected.objects.filter(user=user)

    dict_comprados = {item.character_id: item.is_selected for item in inventario}
    #Listado personajes
    lista_respuestas = []
    for personaje in personajes:
        lista_respuestas.append({
            'id': personaje.id,
            'name': personaje.name,
            'price': personaje.price,
            'base_life': personaje.base_life,
            'base_dmg': personaje.base_dmg,
            'base_defense': personaje.base_defense,
            'base_luck': personaje.base_luck,
            'exp_multiplier': personaje.exp_multiplier,
            'base_movspeed': personaje.base_movspeed,
            'base_atckspeed': personaje.base_atckspeed,
            'purchased': personaje.id in dict_comprados,
            'equiped':dict_comprados.get(personaje.id,False),
        })

    return JsonResponse(lista_respuestas,safe = False, status=200)

@csrf_exempt
def comprar_personaje(request, character_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method must be POST'}, status=405)

    #Validar datos
    session_token = request.headers.get('Authorization')
    character_id = request.headers.get('id')

    if not session_token or not session_token.startswith('Bearer '):
        return JsonResponse({'error': 'Session token no proporcionado'}, status=401)

    session_token = session_token.split(' ')[1]
    try:
        user = User.objects.get(session_token=session_token)
    except User.DoesNotExist:
        return JsonResponse({'error': 'Session token no valido'}, status=401)

    #¿Existe el personaje que quiere comprar?
    try:
        personaje_a_comprar = Character.objects.get(id=character_id)
    except Character.DoesNotExist:
        return JsonResponse({'error': 'El personaje solicitado no existe'}, status=404)

    ya_lo_tiene = UserCharacterSelected.objects.filter(user=user, character=personaje_a_comprar).exists()
    if ya_lo_tiene:
        return JsonResponse({'error': 'Ya tienes este personaje en tu inventario'}, status=400)

    #¿Tiene dinero suficiente?
    if user.special_money < personaje_a_comprar.price:
        return JsonResponse({'error': 'No tienes monedas suficientes'}, status=400)

    user.special_money -= personaje_a_comprar.price
    user.save()
    #Guardas personaje en tu lista sin ponerlo con is_selected = True
    UserCharacterSelected.objects.create(
        user=user,
        character=personaje_a_comprar,
        is_selected=False
    )

    return JsonResponse({
        'mensaje': f'Has comprado a {personaje_a_comprar.name} con éxito',
        'dinero_restante': user.special_money
    }, status=200)


def leaderboard(request):
    if request.method != 'GET':
        return JsonResponse({'error': 'Metodo invalido'}, status=405)


    limite = request.GET.get('limit', 10)

    try:
        limite = int(limite)
    except ValueError:
        limite = 10

    runs = Run.objects.select_related('user').order_by('-time')[:limite]

    leaderboard_data = []
    for run in runs:
        leaderboard_data.append({
            "user": run.user.username,
            "time": run.time,
            "character": run.character.name,
            "lvl_max": run.lvl_max,
        })

    return JsonResponse({'leaderboard': leaderboard_data}, status=200)

@csrf_exempt
def post_runs(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Metodo inválido'}, status=401)
    session_token = request.headers.get('session')
    if not session_token:
        return JsonResponse({'error': 'Session token no valido'}, status=400)
    try:
        user = User.objects.get(session_token=session_token)
    except User.DoesNotExist:
        return JsonResponse({'error': 'Session token no valido'}, status=400)

    try:
        data = json.loads(request.body)
    except json.decoder.JSONDecodeError:
        return JsonResponse({'error':'El cuerpo debe ser un JSON válido'}, status=400)

    time = data.get('time')
    lvl_max = data.get('lvl_max')
    special_money = data.get('special_money')

    try:
        favorite = UserCharacterSelected.objects.get(user=user, is_selected=True)
        character_active = favorite.character
    except UserCharacterSelected.DoesNotExist:
        return JsonResponse({'error': 'El jugador no tiene un personaje equipado'}, status=400)
    new_run = Run.objects.create(
        user=user,
        time = time,
        lvl_max = lvl_max,
        special_money = special_money,
        character = character_active,
    )
    if special_money > 0:
        user.special_money += special_money
        user.save()
    return JsonResponse({'mensaje': 'Run guardada correctamente', 'run_id': new_run.id}, status=201)

@csrf_exempt
def logout_user(request):
    if request.method != 'DELETE':
        return JsonResponse({'error': 'Método invalido'}, status=405)

   #Validar datos
    auth_header = request.headers.get('Authorization')

    # 2. Si no existe o no empieza por "Bearer ", la rechazamos
    if not auth_header or not auth_header.startswith('Bearer '):
        return JsonResponse({'error': 'Session token no proporcionado'}, status=401)

    # 3. Extraemos el token (cortamos por el espacio y cogemos la segunda parte)
    session_token = auth_header.split(' ')[1]
    try:
        user = User.objects.get(session_token=session_token)
    except User.DoesNotExist:
        return JsonResponse({'error': 'Session token no valido'}, status=401)


    #Ponemos el token a None
    user.session_token = ""
    user.save()

    return JsonResponse({'mensaje': 'Sesión cerrada correctamente'}, status=200)

@csrf_exempt
def validar_token(request):
    if request.method == 'GET':
        try:
            auth_header = request.headers.get('Authorization')

            if not auth_header or not auth_header.startswith('Bearer '):
                return JsonResponse({'valido': False, 'error': 'Token no proporcionado'}, status=400)

            token_recibido = auth_header.split(' ')[1]

            user = User.objects.filter(session_token=token_recibido).first()
            favorito = UserCharacterSelected.objects.get(user=user, is_selected=True)

            if user:
                return JsonResponse({
                    'username': user.username,
                    'special_money': user.special_money,
                    'volume': user.volume,
                    'resolution': user.resolution,
                    'is_selected': favorito.character.name
                })
            else:
                return JsonResponse({'valido': False}, status=401)

        except Exception as e:
            return JsonResponse({'valido': False, 'error': str(e)}, status=500)

@csrf_exempt
def post_settings(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Metodo invalido'}, status=401)
    try:
        auth_header = request.headers.get('Authorization')

        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse({'valido': False, 'error': 'Token no proporcionado'}, status=400)

        token_recibido = auth_header.split(' ')[1]

        user = User.objects.get(session_token=token_recibido)

        datos = json.loads(request.body)

        if 'volume' in datos:
            user.volume = int(datos.get('volume'))

        if 'resolution' in datos:
            user.resolution = int(datos.get('resolution'))

        user.save()

        return JsonResponse({'success': True, 'mensaje': 'Ajustes guardados correctamente'}, status=200)

    except User.DoesNotExist:
        return JsonResponse({'valido': False, 'error': 'Token no valido o expirado'}, status=401)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'El formato de los datos no es un JSON valido'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)