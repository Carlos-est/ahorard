def cambiar_formato_fecha(fecha):
    partes_fecha = fecha.split('-')

    return '{}{}{}{}{}'.format(partes_fecha[2],'/', partes_fecha[1],'/', partes_fecha[0])