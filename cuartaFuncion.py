
from sqlalchemy import create_engine
import pymysql
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from datetime import date
#biblioteca Mongo
import pymongo
from pymongo import MongoClient
from bson.json_util import dumps, loads
import time

MONGO_HOST = "200.48.235.251"
MONGO_PUERTO ="27017"
MONGO_PWD = "ciba15153232"
MONGO_USER = "estacionesrd"
MONGO_TIEMPO_FUERA =1000
MONGO_BASEDATOS = "PROYECTORD"
MONGO_COLECCION = "PRETRATAMIENTO"

MONGO_URI = "mongodb://"+ MONGO_USER +":"+ MONGO_PWD + "@"+MONGO_HOST +":" + MONGO_PUERTO + "/"+ MONGO_BASEDATOS 



def convert_formato_fecha(fec):
    fec = datetime.strptime(fec, '%d/%m/%Y')
    #restamos 1 dia que es el de consulta
    fec =fec -timedelta(1)
    fec_unix=int(time.mktime(fec.timetuple()))
    if fec.month < 10:
        fec = str(fec.day)+'/0'+str(fec.month)+'/'+str(fec.year)
    else:
        fec = str(fec.day)+'/'+str(fec.month)+'/'+str(fec.year)
    
    
    return(fec, fec_unix)


def BD_MONGO_NUTRIENTES_VCOLOMBIA(semanas, pais, estacion, fec_unix_usuario):
    fec_inicial_unix = fec_unix_usuario-semanas*86400
    
    try:
        cliente = MongoClient(MONGO_URI, serverSelectionTimeoutMS=MONGO_TIEMPO_FUERA)
        baseDatos = cliente[MONGO_BASEDATOS]
        coleccion=baseDatos[MONGO_COLECCION]
        ##4 CONSULTAS A LA VEZ
        datos = coleccion.aggregate(
                                        [
                                            {"$match": 
                                                {"$and":
                                                        [
                                                            {"pais":pais},
                                                            {"estacion":estacion},
                                                            {"Fecha_D":{"$gt": fec_inicial_unix ,"$lte":fec_unix_usuario}}
                                                        ]
                                                }
                                            },
                                            
                                            {
                                            "$project":{
                                                "_id":0,
                                                "Fecha_D_str":1,
                                                
                                                "Datos.GDD_D":1,
                                                "Datos.Energia_solar_D":1,
                                            }
                                            }

                                        ])

        
        
        semana_gdd = list(datos)
        return semana_gdd
    except pymongo.errors.ServerSelectionTimeoutError as errorTiempo:
        return("Teimpo exedido"+ errorTiempo)
    except pymongo.errors.ConnectionFailure as errorConnexion:
        return("Fallo al conectarse a mongodb" + errorConnexion)


def nutrientes(fec, estacion, rPA, dias):
    pais = 3 #1 peru
    print("Fecha ingresada por el usuario:", fec)
    #convertimos a string y unix y restamos el dia de consulta
    fec_string_usuario, fec_unix_usuario = convert_formato_fecha(fec)
    print("Fecha a ingresar a calculo:", fec_string_usuario)
    ##solicitamos datos
    datos=BD_MONGO_NUTRIENTES_VCOLOMBIA(dias, pais, estacion, fec_unix_usuario)
    
    ##invertir lista
    datos_new = list(reversed(datos))
    Vector_datos=[]
    GDA_acum = 0
    ES_ACUMULADO=0
    RAD_SOLAR = 0
    vector_temp = []
    vector_gda = []
    vector_fecha = []
    vector_gda_acum=[]    
    for k in datos_new:
        gdd = k["Datos"]["GDD_D"]
        GDA_acum += gdd
        fecha = k["Fecha_D_str"]
        energia_solar = k["Datos"]["Energia_solar_D"]
        ES_ACUMULADO += energia_solar
        RAD_SOLAR= k["Datos"]["Energia_solar_D"]/0.0864
        vector_gda.append(gdd)
        vector_gda_acum.append(GDA_acum)
        vector_fecha.append(fecha)
        Vector_datos.append((fecha,round(RAD_SOLAR,2)))
        """ if GDA_acum >= 900:
            break """

    #print("Datos:",Vector_datos)
    matSeca = 1.5*ES_ACUMULADO*(1-np.exp(-0.7*3.5)) #g
    #0.25 es biomasa seca de de toda la planta y divimos entre 1000 para convertir el resultado a kg

    biomasa_planta = matSeca*(10000/rPA)/250
    
    biomasa = biomasa_planta*rPA

    masaNitrogeno_planta = matSeca*(10000/rPA)*0.3*0.00828
    masaPotasio_planta = matSeca*(10000/rPA)*0.3*0.0273
    masaFosforo_planta = matSeca*(10000/rPA)*0.3*0.00124
    
    masaNitrogeno_hectarea = matSeca*(10000/rPA)*0.3*0.00828*(rPA/1000) 
    masaPotasio_hectarea = matSeca*(10000/rPA)*0.3*0.0273*(rPA/1000)
    masaFosforo_hectarea = matSeca*(10000/rPA)*0.3*0.00124*(rPA/1000)
    Vector_datos = list(reversed(Vector_datos))

    return round(masaNitrogeno_planta,2), round(masaNitrogeno_hectarea,2), round(masaPotasio_planta,2), round(masaPotasio_hectarea,2), round(masaFosforo_planta,2), round(masaFosforo_hectarea,2), Vector_datos
