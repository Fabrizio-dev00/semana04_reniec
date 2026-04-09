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
chrome_options.add_argument("--enable-javascript")

# Inicializar navegador
driver = webdriver.Chrome(options=chrome_options)

url = "https://consultaelectoral.onpe.gob.pe/inicio"

# ─── DIAGNÓSTICO ────────────────────────────────────────────────────────
print("Cargando página para diagnóstico...")
driver.get(url)

# Esperar hasta 20s a que Angular termine de renderizar
# buscamos CUALQUIER input o button que aparezca
try:
    WebDriverWait(driver, 20).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )
    # Angular necesita tiempo extra después de readyState complete
    time.sleep(5)
except Exception as e:
    print(f"Timeout esperando página: {e}")

driver.save_screenshot("/app/pagina.png")
with open("/app/pagina.html", "w", encoding="utf-8") as f:
    f.write(driver.page_source)

# Imprimir todos los inputs encontrados para diagnóstico
inputs = driver.find_elements(By.XPATH, "//input")
print(f"Inputs encontrados: {len(inputs)}")
for i, inp in enumerate(inputs):
    print(f"  Input {i}: type='{inp.get_attribute('type')}' "
          f"name='{inp.get_attribute('name')}' "
          f"id='{inp.get_attribute('id')}' "
          f"placeholder='{inp.get_attribute('placeholder')}'")

botones = driver.find_elements(By.XPATH, "//button")
print(f"Botones encontrados: {len(botones)}")
for i, b in enumerate(botones):
    print(f"  Botón {i}: text='{b.text}' id='{b.get_attribute('id')}'")

print("Archivos guardados: pagina.png y pagina.html")
# ────────────────────────────────────────────────────────────────────────

for _, fila in df.iterrows():
    dni = str(fila["DNI"]).strip()

    try:
        driver.get(url)

        # Esperar a que Angular cargue completamente
        WebDriverWait(driver, 20).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        time.sleep(5)  # Angular necesita tiempo extra

        # Buscar input (intentamos varios selectores posibles)
        input_dni = None
        selectores = [
            "//input[@type='text']",
            "//input[@type='number']",
            "//input[contains(@placeholder,'DNI') or contains(@placeholder,'dni')]",
            "//input[contains(@id,'dni') or contains(@id,'DNI')]",
            "//input[contains(@name,'dni') or contains(@name,'DNI')]",
            "//input",  # cualquier input como último recurso
        ]

        for selector in selectores:
            try:
                elementos = driver.find_elements(By.XPATH, selector)
                if elementos:
                    input_dni = elementos[0]
                    print(f"DNI {dni}: input encontrado con selector '{selector}'")
                    break
            except Exception:
                continue

        if input_dni is None:
            driver.save_screenshot(f"/app/error_dni_{dni}.png")
            raise Exception("No se encontró ningún input en la página")

        input_dni.clear()
        input_dni.send_keys(dni)

        # Buscar botón consultar
        boton = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//button[contains(translate(., 'CONSULTAR', 'consultar'), 'consultar')]"
            ))
        )
        boton.click()

        time.sleep(6)

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

# Guardar resultados
salida = pd.DataFrame(resultados)
salida.to_excel("resultados.xlsx", index=False)
print("Proceso terminado. Archivo generado: resultados.xlsx")