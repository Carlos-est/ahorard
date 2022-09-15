def cambiar_formato_fecha(fecha):
    partes_fecha = fecha.split('-')

    return '{}{}{}{}{}'.format(partes_fecha[2],'/', partes_fecha[1],'/', partes_fecha[0])


from App import baseDatos, coleccion
def estaciones(Id_estacion):
    dict_estaciones = {"1": "AMINA", "2":"HATILLO PALMA", "3":"HATO AL MEDIO", "4":"JULIANA", 
    "5":"LA CAIDA", "6":"MAO", "7":"MONTECRISTI","8": "SAN ISIDRO"}
    estacionName=dict_estaciones[str(Id_estacion)]
    return estacionName

MONGO_COLECCION = "PRETRATAMIENTO"
coleccion=baseDatos[MONGO_COLECCION]
def estado_estaciones(pais):
    estaciones_disponibles = coleccion.aggregate(
                                    [                   
                                        {
                                            "$group":
                                                    {
                                                        "_id": "",
                                                        "estacion":{"$max":"$estacion"}
                                                    }
                                        }
                                    ]
                                )
    estaciones_disponibles=list(estaciones_disponibles)
    cantidad_Estaciones = estaciones_disponibles[0]["estacion"]
    print("cantidad de estaciones:", cantidad_Estaciones)
    #solicitamos los ultimos registros de cada estacion
    Registro_Estaciones = []
    
    for estacion in range(1,cantidad_Estaciones+1): #se suma uno porque Rangue cuenta desde Cero por lo tanto reduce una unidad
        datos = coleccion.aggregate(
                                    [
                                        {"$match": 
                                            {"$and":
                                                    [
                                                        {"pais":pais},
                                                        {"estacion":estacion},
                                                    ]
                                            }
                                        },
                                        {
                                        "$sort":{
                                            "_id":-1
                                                }
                                        },
                                        {
                                        "$limit":1
                                        },
                                    ])
        datos = list(datos)
        estacion_ = datos[0]["estacion"]
        Nombre_ = estaciones(estacion_)
        fecha_ = datos[0]["Fecha_D_str"]

        Registro_Estaciones.append((estacion_,Nombre_, fecha_))
        
    print("registro de staciones", Registro_Estaciones)
    return cantidad_Estaciones, Registro_Estaciones


def Visita(mail):
    from datetime import datetime
    visitas = {"Visita": 1,"usuario": mail ,"Tipo":"Aplicativo web" ,"Fecha_utc": datetime.utcnow(), "Fecha_local": datetime.now()}
    return visitas



def generate_random_string():
    import random
    import string
    length=8
    letters = string.ascii_lowercase
    rand_string = ''.join(random.choice(letters) for i in range(length))
    return rand_string

