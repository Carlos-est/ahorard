
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
import calendar

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
    print("fecha restada:", fec)
    fec_unix=int(time.mktime(fec.timetuple()))
    print("fecha calculada del anterior:", fec_unix)
    fe_unix = calendar.timegm(fec.utctimetuple())
    print("fecha nueva calculada del anterior:", fe_unix)
    if fec.month < 10:
        fec = str(fec.day)+'/0'+str(fec.month)+'/'+str(fec.year)
    else:
        fec = str(fec.day)+'/'+str(fec.month)+'/'+str(fec.year)
    
    
    return(fec, fec_unix)

def BD_MONGO_RIEGO_DEMANDA(pais, estacion, fec_unix_usuario):
    fec_inicial_unix = fec_unix_usuario-7*86400
    print("ts inicial:", fec_inicial_unix)
    print("ts usuario:", fec_unix_usuario)
    #fec_unix_usuario=fec_unix_usuario+86400
    
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
                                                
                                                "Datos.ET_D":1,
                                                "Datos.Precipitacion_D":1,
                                            }
                                            }

                                        ])

        
        
        semana_gdd = list(datos)
        return semana_gdd
    except pymongo.errors.ServerSelectionTimeoutError as errorTiempo:
        return("Teimpo exedido"+ errorTiempo)
    except pymongo.errors.ConnectionFailure as errorConnexion:
        return("Fallo al conectarse a mongodb" + errorConnexion)

def nHidricaDemanda(fec, estacion, tipo, tipo_riego):
    pais = 3 #1 peru
    print("Fecha ingresada por el usuario:", fec)
    #convertimos a string y unix y restamos el dia de consulta
    fec_string_usuario, fec_unix_usuario = convert_formato_fecha(fec)
    print("Fecha a ingresar a calculo:", fec_string_usuario)
    ##solicitamos datos
    datos=BD_MONGO_RIEGO_DEMANDA(pais, estacion, fec_unix_usuario)
    print("datos:", datos)
    ###calculo
    ET_acc = 0
    precip_acc = 0
    agua_aprove = {'arenosa':2.5, 'arcillosa':7, 'franco':4.75}
    den_ap_suelo = {'arenosa':1.65, 'arcillosa':1.3, 'franco':1.25}
    cap_suelo = den_ap_suelo[tipo]*500*agua_aprove[tipo]
    suelo_infil_lluvia = ET_acc + cap_suelo
    #unimos datos para la grafica de la evapotranspiracion
    Vector_Grafica=[]
    evp_cultivo=0

    for k in datos:
        fecha = k["Fecha_D_str"]
        et = k["Datos"]["ET_D"]
        ET_acc += et
        inc_lluvia = k["Datos"]["Precipitacion_D"]
        evp_cultivo += round(et*1.1,2)
        #print("Fecha:", fecha, " ","Temperatura:", temperatura , " ", "GDD:", gdd)
        if inc_lluvia > 5:
            precip_acc += inc_lluvia
        Vector_Grafica.append((fecha, round(et*1.1,2), round(inc_lluvia,2)))
    
    if suelo_infil_lluvia < precip_acc:
        lluvia_efectiva = suelo_infil_lluvia
    else:
        lluvia_efectiva = precip_acc
    ef_riego = {'inundación':0.5,'microaspersión':0.7,'goteo':0.9}
    NH = (ET_acc*1.1 - lluvia_efectiva)*10/ef_riego[tipo_riego]
    if NH < 0:
        NH = 0
    Deficit=evp_cultivo-lluvia_efectiva
    #print("lluvia efectiva:", lluvia_efectiva)
    if Deficit <= 0:
        Deficit=0
    print("vector grafica:", Vector_Grafica)
    return round(NH,2), Vector_Grafica, round(evp_cultivo,2), round(Deficit,2)

### funion b : hidrica

def BD_MONGO_RIEGO(dias, pais, estacion, fec_unix_usuario):
    fec_inicial_unix = fec_unix_usuario-dias*86400
    
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
                                                
                                                "Datos.ET_D":1,
                                                "Datos.Precipitacion_D":1,
                                            }
                                            }

                                        ])

        
        
        semana_gdd = list(datos)
        return semana_gdd
    except pymongo.errors.ServerSelectionTimeoutError as errorTiempo:
        return("Teimpo exedido"+ errorTiempo)
    except pymongo.errors.ConnectionFailure as errorConnexion:
        return("Fallo al conectarse a mongodb" + errorConnexion)


def nHidrica(dias, fec, estacion, tipo, tipo_riego):
    pais = 3 #1 peru
    print("Fecha ingresada por el usuario:", fec)
    #convertimos a string y unix y restamos el dia de consulta
    fec_string_usuario, fec_unix_usuario = convert_formato_fecha(fec)
    print("Fecha a ingresar a calculo:", fec_string_usuario)
    ##solicitamos datos
    datos=BD_MONGO_RIEGO(dias, pais, estacion, fec_unix_usuario)
    ###calculo
    ET_acc = 0
    precip_acc = 0
    agua_aprove = {'arenosa':2.5, 'arcillosa':7, 'franco':4.75}
    den_ap_suelo = {'arenosa':1.65, 'arcillosa':1.3, 'franco':1.25}
    cap_suelo = den_ap_suelo[tipo]*500*agua_aprove[tipo]
    suelo_infil_lluvia = ET_acc + cap_suelo
    #unimos datos para la grafica de la evapotranspiracion
    Vector_Grafica=[]
    evp_cultivo=0

    for k in datos:
        fecha = k["Fecha_D_str"]
        et = k["Datos"]["ET_D"]
        ET_acc += et
        inc_lluvia = k["Datos"]["Precipitacion_D"]
        evp_cultivo += round(et*1.1,2)
        #print("Fecha:", fecha, " ","Temperatura:", temperatura , " ", "GDD:", gdd)
        if inc_lluvia > 5:
            precip_acc += inc_lluvia
        Vector_Grafica.append((fecha, round(et*1.1,2), round(inc_lluvia,2)))
    
    if suelo_infil_lluvia < precip_acc:
        lluvia_efectiva = suelo_infil_lluvia
    else:
        lluvia_efectiva = precip_acc
    ef_riego = {'inundación':0.5,'microaspersión':0.7,'goteo':0.9}
    NH = (ET_acc*1.1 - lluvia_efectiva)*10/ef_riego[tipo_riego]
    if NH < 0:
        NH = 0
    Deficit=evp_cultivo-lluvia_efectiva
    #print("lluvia efectiva:", lluvia_efectiva)
    return round(NH/10,2), Vector_Grafica, round(evp_cultivo,2), round(Deficit,2)

##funcion c : intervalo

def BD_MONGO_INTERVALO(dias, pais, estacion, fec_unix_usuario):
    fec_inicial_unix = fec_unix_usuario-dias*86400
    
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
                                                
                                                "Datos.ET_D":1,
                                                "Datos.Precipitacion_D":1,
                                            }
                                            }

                                        ])

        
        
        semana_gdd = list(datos)
        return semana_gdd
    except pymongo.errors.ServerSelectionTimeoutError as errorTiempo:
        return("Teimpo exedido"+ errorTiempo)
    except pymongo.errors.ConnectionFailure as errorConnexion:
        return("Fallo al conectarse a mongodb" + errorConnexion)


def nHidricaIntervalo(dias, fec, estacion, tipo, tipo_riego):
    pais = 3 #1 peru
    print("Fecha ingresada por el usuario:", fec)
    #convertimos a string y unix y restamos el dia de consulta
    fec_string_usuario, fec_unix_usuario = convert_formato_fecha(fec)
    print("Fecha a ingresar a calculo:", fec_string_usuario)
    ##solicitamos datos
    datos=BD_MONGO_INTERVALO(dias, pais, estacion, fec_unix_usuario)
    ###calculo
    ET_acc = 0
    precip_acc = 0
    agua_aprove = {'arenosa':2.5, 'arcillosa':7, 'franco':4.75}
    den_ap_suelo = {'arenosa':1.65, 'arcillosa':1.3, 'franco':1.25}
    cap_suelo = den_ap_suelo[tipo]*500*agua_aprove[tipo]
    suelo_infil_lluvia = ET_acc + cap_suelo
    #unimos datos para la grafica de la evapotranspiracion
    Vector_Grafica=[]
    evp_cultivo=0

    for k in datos:
        fecha = k["Fecha_D_str"]
        et = k["Datos"]["ET_D"]
        ET_acc += et
        inc_lluvia = k["Datos"]["Precipitacion_D"]
        evp_cultivo += round(et*1.1,2)
        #print("Fecha:", fecha, " ","Temperatura:", temperatura , " ", "GDD:", gdd)
        if inc_lluvia > 5:
            precip_acc += inc_lluvia
        Vector_Grafica.append((fecha, round(et*1.1,2), round(inc_lluvia,2)))
    
    if suelo_infil_lluvia < precip_acc:
        lluvia_efectiva = suelo_infil_lluvia
    else:
        lluvia_efectiva = precip_acc
    ef_riego = {'inundación':0.5,'microaspersión':0.7,'goteo':0.9}
    NH = (ET_acc*1.1 - lluvia_efectiva)*10/ef_riego[tipo_riego]
    if NH < 0:
        NH = 0
    prom_evp_cultivo=evp_cultivo/dias ##sacamos el promedio de evapo del cultivo por dia
    intervalo_30= (30+lluvia_efectiva)/prom_evp_cultivo ###a 30 le sumamos la lluvia efectiva y dividimos entre el promedio
    #print("intervalo 30:", intervalo_30)
    intervalo_50= (50+lluvia_efectiva)/prom_evp_cultivo
    #print("intervalo 50:", intervalo_50)
    intervalo_70= (70+lluvia_efectiva)/prom_evp_cultivo
    #print("intervalo 70:", intervalo_70)
    return round(NH/10,2), Vector_Grafica, round(evp_cultivo,2), round(intervalo_30, 1), round(intervalo_50,1), round(intervalo_70,1)



