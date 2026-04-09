from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
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

# Inicializar navegador
driver = webdriver.Chrome(options=chrome_options)

url = "https://consultaelectoral.onpe.gob.pe/inicio"

# ─── DIAGNÓSTICO: captura solo el primer DNI ───────────────────────────
print("Cargando página para diagnóstico...")
driver.get(url)
time.sleep(6)

driver.save_screenshot("/app/pagina.png")
with open("/app/pagina.html", "w", encoding="utf-8") as f:
    f.write(driver.page_source)

print("Archivos guardados: pagina.png y pagina.html")
print("Revisa pagina.png para ver qué cargó el navegador.")
# ───────────────────────────────────────────────────────────────────────

for _, fila in df.iterrows():
    dni = str(fila["DNI"]).strip()

    try:
        driver.get(url)
        time.sleep(6)

        # Esperar hasta 15s a que aparezca cualquier input visible
        try:
            input_dni = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.XPATH, "//input[@type='text']"))
            )
        except Exception:
            # Si no aparece, guardar screenshot de ese momento
            driver.save_screenshot(f"/app/error_dni_{dni}.png")
            raise Exception("No se encontró el input del DNI después de 15 segundos")

        input_dni.clear()
        input_dni.send_keys(dni)

        # Hacer clic en Consultar
        boton = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//button[contains(translate(., 'CONSULTAR', 'consultar'), 'consultar')]"
            ))
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