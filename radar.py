import requests
from bs4 import BeautifulSoup
import os

print("RADAR MINERO V21 RECLUTADOR — PORTALES + MINERAS")

# ==========================================
# TELEGRAM
# ==========================================

TOKEN = os.environ["TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

def enviar(msg):

    try:

        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": msg}
        )

    except:

        print("Error Telegram")


# ==========================================
# MEMORIA
# ==========================================

ARCHIVO = "memoria.txt"

def cargar_memoria():

    try:

        with open(ARCHIVO,"r") as f:
            return set(f.read().splitlines())

    except:
        return set()


def guardar_memoria(mem):

    with open(ARCHIVO,"w") as f:

        for link in mem:
            f.write(link+"\n")


memoria = cargar_memoria()


# ==========================================
# FILTRO PROFESIONAL MINERO
# ==========================================

CARGOS = [

"supervisor",
"jefe",
"administrador",
"contract administrator",
"contract manager",
"planner",
"planificador",
"ingeniero mantenimiento",
"ingeniero mantencion",
"maintenance supervisor",
"supervisor operaciones",

]

EXCLUIR = [

"practica",
"práctica",
"trainee",
"alumno",
"operador",
"operaria"

]


def filtro(texto):

    texto = texto.lower()

    if any(x in texto for x in EXCLUIR):

        return False

    if any(x in texto for x in CARGOS):

        return True

    return False


# ==========================================
# FUNCION GENERICA
# ==========================================

def buscar(nombre,url,dominio):

    print("Buscando:",nombre)

    lista=[]

    try:

        r=requests.get(url,timeout=20)

        soup=BeautifulSoup(r.text,"html.parser")

        for link in soup.find_all("a"):

            titulo=link.get_text(strip=True)

            href=link.get("href")

            if not titulo or not href:
                continue

            if href.startswith("/"):

                href=dominio+href


            texto=titulo+" "+nombre

            if filtro(texto):

                lista.append({

                "titulo":titulo,
                "empresa":nombre,
                "link":href

                })

                print("OK:",titulo)

    except:

        print("Error en",nombre)

    return lista


# ==========================================
# PORTALES EMPLEO CHILE
# ==========================================

empleos=[]


# MINERAS

empleos+=buscar(

"Codelco",
"https://empleos.codelco.cl/",
"https://empleos.codelco.cl"

)


empleos+=buscar(

"BHP",
"https://jobs.bhp.com/search/",
"https://jobs.bhp.com"

)


empleos+=buscar(

"Finning",
"https://finning.csod.com/",
"https://finning.csod.com"

)


empleos+=buscar(

"Komatsu",
"https://komatsu.jobs/jobs",
"https://komatsu.jobs"

)



# PORTALES

empleos+=buscar(

"Chiletrabajos",
"https://www.chiletrabajos.cl/",
"https://www.chiletrabajos.cl"

)


empleos+=buscar(

"Trabajando",
"https://www.trabajando.cl/",
"https://www.trabajando.cl"

)


empleos+=buscar(

"Indeed",
"https://cl.indeed.com/jobs?q=mineria",
"https://cl.indeed.com"

)



# ==========================================
# ELIMINAR DUPLICADOS
# ==========================================

unicos=[]
vistos=set()

for e in empleos:

    if e["link"] not in vistos:

        unicos.append(e)
        vistos.add(e["link"])

empleos=unicos


# ==========================================
# FILTRAR NUEVOS
# ==========================================

nuevos=[]

for e in empleos:

    if e["link"] not in memoria:

        nuevos.append(e)

        memoria.add(e["link"])



# ==========================================
# TELEGRAM
# ==========================================

enviar("RADAR V21 RECLUTADOR INICIADO")


if nuevos:

    msg="EMPLEOS NUEVOS\n\n"

    for e in nuevos[:15]:

        msg+=f"{e['titulo']}\n{e['empresa']}\n{e['link']}\n\n"


    enviar(msg)


else:

    enviar("Sin empleos nuevos en portales y mineras")


enviar("RADAR V21 FINALIZADO")



# ==========================================
# GUARDAR MEMORIA
# ==========================================

guardar_memoria(memoria)
