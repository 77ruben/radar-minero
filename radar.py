import requests
from bs4 import BeautifulSoup
import os

print("RADAR MINERO V24 ULTRA — MINERAS + PORTALES + CONTRATISTAS + LINKEDIN")

# ============================
# TELEGRAM
# ============================

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

# ============================
# MEMORIA
# ============================

FICH="memoria.txt"

def cargar():
    try:
        with open(FICH) as f:
            return set(f.read().splitlines())
    except:
        return set()

def guardar(mem):
    with open(FICH,"w") as f:
        for x in mem:
            f.write(x+"\n")

memoria=cargar()

# ============================
# FILTRO AVANZADO
# ============================

CLAVES=[

"supervisor",
"jefe",
"administrador",
"administracion de contratos",
"contract",
"planner",
"planificador",
"operations",
"operaciones",
"maintenance",
"mantencion",
"mantenimiento",
"turno",
"7x7",
"14x14",
"4x3",
"turno mina",
"maintenance supervisor",

]

EXC=[

"practica","práctica","alumno","trainee","operador","operaria","sueldos","salary"

]

def filtro(txt):
    t=txt.lower()
    if any(x in t for x in EXC):
        return False
    return any(x in t for x in CLAVES)

# ============================
# SCRAP HTML GENERICO
# ============================

def buscar_html(nombre,url,dominio,selector):
    lista=[]
    try:
        r=requests.get(url,timeout=20,headers={"User-Agent":"Mozilla/5.0"})
        soup=BeautifulSoup(r.text,"html.parser")
        for item in soup.select(selector):
            titulo=item.get_text(strip=True)
            href=item.get("href")
            if not titulo or not href:
                continue
            if href.startswith("/"):
                href=dominio+href
            if filtro(titulo+" "+nombre):
                lista.append({
                "titulo":titulo,
                "empresa":nombre,
                "link":href
                })
                print("OK",nombre,titulo)
    except:
        print("Error",nombre)
    return lista

# ============================
# SCRAP KINROSS
# ============================

def kinross():
    nombre="Kinross"
    lista=[]
    try:
        url="https://jobs.kinross.com/go/Puestos-para-profesionales"
        r=requests.get(url,timeout=20,headers={"User-Agent":"Mozilla/5.0"})
        soup=BeautifulSoup(r.text,"html.parser")
        for card in soup.select(".jobs__item a"):
            titulo=card.get_text(strip=True)
            href=card.get("href")
            if href and href.startswith("/"):
                href="https://jobs.kinross.com"+href
            if filtro(titulo):
                lista.append({
                "titulo":titulo,
                "empresa":nombre,
                "link":href
            })
            print("OK Kinross",titulo)
    except:
        print("Error Kinross")
    return lista

# ============================
# SCRAP BHP API
# ============================

def bhp_api():
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

# ============================
# BUSCADORES
# ============================

empleos=[]

# Mineras
empleos+=buscar_html(
"Codelco",
"https://empleos.codelco.cl/search/?q=",
"https://empleos.codelco.cl",
"a"
)

empleos+=buscar_html(
"Antofagasta Minerals",
"https://www.aminerals.cl/carreras",
"https://www.aminerals.cl",
"a"
)

empleos+=buscar_html(
"Anglo American",
"https://jobs.angloamerican.com/search/",
"https://jobs.angloamerican.com",
"a"
)

empleos+=buscar_html(
"Collahuasi",
"https://www.collahuasi.cl/personas/trabaja-con-nosotros/",
"https://www.collahuasi.cl",
"a"
)

empleos+=kinross()

empleos+=bhp_api()

# Contratistas
empleos+=buscar_html(
"Finning",
"https://finning.csod.com/",
"https://finning.csod.com",
"a"
)

empleos+=buscar_html(
"Komatsu",
"https://komatsu.jobs/jobs",
"https://komatsu.jobs",
"a"
)

empleos+=buscar_html(
"Enaex",
"https://enaex.jobs/jobs",
"https://enaex.jobs",
"a"
)

empleos+=buscar_html(
"Orica",
"https://orica.jobs/jobs",
"https://orica.jobs",
"a"
)

empleos+=buscar_html(
"Metso",
"https://metso.jobs/jobs",
"https://metso.jobs",
"a"
)

# ============================
# ELIMINAR DUPLICADOS
# ============================

unicos=[]
vistos=set()

for e in empleos:
    if e["link"] not in vistos:
        unicos.append(e)
        vistos.add(e["link"])

# ============================
# FILTRAR NUEVOS
# ============================

nuevos=[]

for e in unicos:
    if e["link"] not in memoria:
        nuevos.append(e)
        memoria.add(e["link"])

# ============================
# TELEGRAM
# ============================

enviar("RADAR V24 ULTRA INICIADO")

if nuevos:
    txt="NUEVOS EMPLEOS MINEROS\n\n"
    for e in nuevos[:25]:
        txt+=f"{e['titulo']}\n{e['empresa']}\n{e['link']}\n\n"
    enviar(txt)
else:
    enviar("Sin empleos nuevos detectados")

enviar("RADAR V24 ULTRA FINALIZADO")

# Guardar memoria
guardar(memoria)
