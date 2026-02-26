import requests
from bs4 import BeautifulSoup
import os

print("RADAR MINERO V23 PRO — MINERAS TOP CHILE + API")

TOKEN = os.environ["TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

def enviar(msg):

    try:

        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": msg}
        )

    except:

        pass


# ==========================
# MEMORIA
# ==========================

ARCHIVO="memoria.txt"

def cargar():

    try:

        with open(ARCHIVO) as f:
            return set(f.read().splitlines())

    except:

        return set()


def guardar(mem):

    with open(ARCHIVO,"w") as f:

        for x in mem:

            f.write(x+"\n")


memoria=cargar()


# ==========================
# FILTRO PRO
# ==========================

CARGOS=[

"supervisor",
"jefe",
"administrador",
"planner",
"planificador",
"maintenance",
"mantencion",
"mantenimiento",
"operations",
"operaciones",
"contract"

]

EXCLUIR=[

"sueldos",
"salary",
"practica",
"práctica",
"alumno",
"trainee"

]

def filtro(txt):

    txt=txt.lower()

    if any(x in txt for x in EXCLUIR):

        return False

    return any(x in txt for x in CARGOS)


# ==========================
# BUSCAR HTML
# ==========================

def buscar(nombre,url,dominio,selector):

    lista=[]

    try:

        r=requests.get(url,timeout=20,headers={
        "User-Agent":"Mozilla/5.0"
        })

        soup=BeautifulSoup(r.text,"html.parser")

        for item in soup.select(selector):

            titulo=item.get_text(strip=True)

            link=item.get("href")

            if not titulo or not link:

                continue

            if link.startswith("/"):

                link=dominio+link

            if filtro(titulo):

                lista.append({

                "titulo":titulo,
                "empresa":nombre,
                "link":link

                })

                print("OK",nombre,titulo)

    except:

        print("Error",nombre)


    return lista


# ==========================
# BUSCAR API BHP REAL
# ==========================

def bhp():

    lista=[]

    try:

        url="https://jobs.bhp.com/api/jobs"

        r=requests.get(url,timeout=20)

        data=r.json()

        for job in data:

            titulo=job.get("title","")

            link="https://jobs.bhp.com"+job.get("url","")

            if filtro(titulo):

                lista.append({

                "titulo":titulo,
                "empresa":"BHP",
                "link":link

                })

                print("OK BHP",titulo)

    except:

        print("Error BHP API")


    return lista


# ==========================
# MINERAS CHILE
# ==========================

empleos=[]


empleos+=buscar(

"Codelco",
"https://empleos.codelco.cl/search/?q=",
"https://empleos.codelco.cl",
"a"

)


empleos+=buscar(

"Antofagasta Minerals",
"https://www.aminerals.cl/carreras",
"https://www.aminerals.cl",
"a"

)


empleos+=buscar(

"Anglo American",
"https://jobs.angloamerican.com/search/",
"https://jobs.angloamerican.com",
"a"

)


empleos+=buscar(

"Collahuasi",
"https://www.collahuasi.cl/personas/trabaja-con-nosotros/",
"https://www.collahuasi.cl",
"a"

)


empleos+=buscar(

"Kinross",
"https://jobs.kinross.com/",
"https://jobs.kinross.com",
"a"

)


empleos+=buscar(

"Sierra Gorda",
"https://www.sierragorda.cl/trabaja-con-nosotros/",
"https://www.sierragorda.cl",
"a"

)


empleos+=bhp()


# ==========================
# ELIMINAR DUPLICADOS
# ==========================

unicos=[]
links=set()

for e in empleos:

    if e["link"] not in links:

        unicos.append(e)

        links.add(e["link"])


# ==========================
# FILTRAR NUEVOS
# ==========================

nuevos=[]

for e in unicos:

    if e["link"] not in memoria:

        nuevos.append(e)

        memoria.add(e["link"])


# ==========================
# TELEGRAM
# ==========================

enviar("RADAR V23 PRO INICIADO")


if nuevos:

    msg="NUEVOS EMPLEOS MINEROS\n\n"

    for e in nuevos[:20]:

        msg+=f"{e['titulo']}\n{e['empresa']}\n{e['link']}\n\n"


    enviar(msg)

else:

    enviar("Sin empleos nuevos detectados")


enviar("RADAR V23 PRO FINALIZADO")


guardar(memoria)
