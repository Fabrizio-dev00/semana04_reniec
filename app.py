from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time

# Leer archivo Excel
df = pd.read_excel("dnis.xlsx")

resultados = []

# Configuración de Chrome para Python 3.13
chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")

# Evita problemas de compatibilidad en Windows / Python 3.13
chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])

# Inicializar navegador
driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=chrome_options
)

url = "https://consultaelectoral.onpe.gob.pe/inicio"

for _, fila in df.iterrows():
    dni = str(fila["DNI"]).strip()

    try:
        driver.get(url)
        time.sleep(4)

        # Buscar el input donde se ingresa el DNI
        input_dni = driver.find_element(By.XPATH, "//input[@type='text']")
        input_dni.clear()
        input_dni.send_keys(dni)

        # Buscar el botón Consultar
        boton = driver.find_element(
            By.XPATH,
            "//button[contains(translate(., 'CONSULTAR', 'consultar'), 'consultar')]"
        )
        boton.click()

        time.sleep(5)

        pagina = driver.page_source.lower()

        if "miembro de mesa" in pagina:
            estado = "SI"

            try:
                ubicacion = driver.find_element(
                    By.XPATH,
                    "//[contains(text(),'Ubicación')]/following::[1]"
                ).text.strip()
            except Exception:
                ubicacion = "No encontrada"

            try:
                 direccion = driver.find_element(
                     By.XPATH,
                     "//[contains(text(),'Dirección')]/following::[1]"
                ).text.strip()
            except Exception:
                direccion = "No encontrada"

        else:
            estado = "NO"
            ubicacion = "-"
            direccion = "-"

        resultados.append({
            "DNI": dni,
            "Miembro de Mesa": estado,
            "Ubicación": ubicacion,
            "Dirección Local": direccion
        })

        print(f"DNI {dni}: {estado}")

    except Exception as e:
        print(f"Error con DNI {dni}: {e}")

        resultados.append({
            "DNI": dni,
            "Miembro de Mesa": "ERROR",
            "Ubicación": str(e),
            "Dirección Local": "-"
        })

driver.quit()

# Guardar resultados
salida = pd.DataFrame(resultados)
salida.to_excel("resultados.xlsx", index=False)

print("Proceso terminado. Archivo generado: resultados.xlsx")