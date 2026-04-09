from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import pandas as pd
import time

# Leer archivo Excel
df = pd.read_excel("dnis.xlsx")

resultados = []

# Configuración de Chrome para Docker
chrome_options = Options()
chrome_options.binary_location = "/usr/bin/chromium"
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920,1080")

# Inicializar navegador (usa el chromium instalado en el sistema)
driver = webdriver.Chrome(options=chrome_options)

url = "https://consultaelectoral.onpe.gob.pe/inicio"

for _, fila in df.iterrows():
    dni = str(fila["DNI"]).strip()

    try:
        driver.get(url)
        time.sleep(4)

        # Ingresar el DNI
        input_dni = driver.find_element(By.XPATH, "//input[@type='text']")
        input_dni.clear()
        input_dni.send_keys(dni)

        # Hacer clic en Consultar
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
                    "//[contains(text(),'Ubicación') or contains(text(),'ubicación')]/following::[1]"
                ).text.strip()
            except Exception:
                ubicacion = "No encontrada"

            try:
                direccion = driver.find_element(
                    By.XPATH,
                    "//[contains(text(),'Dirección') or contains(text(),'dirección')]/following::[1]"
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

# Guardar resultados en Excel
salida = pd.DataFrame(resultados)
salida.to_excel("resultados.xlsx", index=False)

print("Proceso terminado. Archivo generado: resultados.xlsx")