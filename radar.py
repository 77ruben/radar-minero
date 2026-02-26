import requests
from bs4 import BeautifulSoup
import os

print("RADAR MINERO V22 ELITE — SCRAPING REAL")

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


# MEMORIA

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


# FILTRO

CARGOS=[

"supervisor",
"jefe",
"administrador",
"planificador",
"ingeniero",

]

def filtro(txt):

    txt=txt.lower()

    return any(x in txt for x in CARGOS)


# BUSCAR

def buscar(nombre,url,dominio,selector):

    lista=[]

    try:

        r=requests.get(url,timeout=20,headers={
        "User-Agent":"Mozilla/5.0"
        })

        soup=BeautifulSoup(r.text,"html.parser")

        for item in soup.select(selector):

            titulo=item.get_text(strip=True)

            href=item.get("href")

            if href and href.startswith("/"):

                href=dominio+href

            if filtro(titulo):

                lista.append({

                "titulo":titulo,
                "empresa":nombre,
                "link":href

                })

                print("OK",titulo)

    except:

        print("Error",nombre)

    return lista



empleos=[]


# CODELCO REAL

empleos+=buscar(

"Codelco",

"https://empleos.codelco.cl/search/?q=",

"https://empleos.codelco.cl",

"a"

)


# INDEED REAL

empleos+=buscar(

"Indeed",

"https://cl.indeed.com/jobs?q=supervisor+mineria",

"https://cl.indeed.com",

"a"

)


# CHILETRABAJOS REAL

empleos+=buscar(

"Chiletrabajos",

"https://www.chiletrabajos.cl/busqueda/?q=mineria",

"https://www.chiletrabajos.cl",

"a"

)



# LIMPIAR DUPLICADOS

unicos=[]
links=set()

for e in empleos:

    if e["link"] not in links:

        unicos.append(e)
        links.add(e["link"])


# FILTRAR NUEVOS

nuevos=[]

for e in unicos:

    if e["link"] not in memoria:

        nuevos.append(e)
        memoria.add(e["link"])



# TELEGRAM

enviar("RADAR V22 ELITE INICIADO")


if nuevos:

    msg="NUEVOS EMPLEOS\n\n"

    for e in nuevos[:20]:

        msg+=f"{e['titulo']}\n{e['empresa']}\n{e['link']}\n\n"

    enviar(msg)

else:

    enviar("Sin empleos nuevos detectados")


enviar("RADAR V22 FINALIZADO")


guardar(memoria)
