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
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

driver = webdriver.Chrome(options=chrome_options)

url = "https://consultaelectoral.onpe.gob.pe/inicio"

def esperar_angular(driver, timeout=30):
    """Espera a que Angular termine de renderizar el contenido."""
    # 1. Esperar readyState complete
    WebDriverWait(driver, timeout).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )
    # 2. Esperar a que app-root tenga hijos (Angular renderizó)
    WebDriverWait(driver, timeout).until(
        lambda d: d.execute_script(
            "return document.querySelector('app-root') && "
            "document.querySelector('app-root').children.length > 0"
        )
    )
    # 3. Esperar a que aparezca cualquier input o button
    WebDriverWait(driver, timeout).until(
        lambda d: len(d.find_elements(By.XPATH, "//input | //button")) > 0
    )

# ─── DIAGNÓSTICO ────────────────────────────────────────────────────────
print("Cargando página para diagnóstico...")
driver.get(url)

try:
    esperar_angular(driver)
    print("Angular cargó correctamente")
except Exception as e:
    print(f"Timeout esperando Angular: {e}")

driver.save_screenshot("/app/pagina.png")
with open("/app/pagina.html", "w", encoding="utf-8") as f:
    f.write(driver.page_source)

inputs = driver.find_elements(By.XPATH, "//input")
print(f"Inputs encontrados: {len(inputs)}")
for i, inp in enumerate(inputs):
    print(f"  Input {i}: type='{inp.get_attribute('type')}' "
          f"id='{inp.get_attribute('id')}' "
          f"placeholder='{inp.get_attribute('placeholder')}' "
          f"formcontrolname='{inp.get_attribute('formcontrolname')}'")

botones = driver.find_elements(By.XPATH, "//button")
print(f"Botones encontrados: {len(botones)}")
for i, b in enumerate(botones):
    print(f"  Botón {i}: text='{b.text}' id='{b.get_attribute('id')}'")
# ────────────────────────────────────────────────────────────────────────

for _, fila in df.iterrows():
    dni = str(fila["DNI"]).strip()

    try:
        driver.get(url)
        esperar_angular(driver)

        # Buscar input del DNI
        input_dni = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//input"))
        )
        input_dni.clear()
        input_dni.send_keys(dni)

        # Buscar y clickear botón Consultar
        boton = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//button[contains(translate(., 'CONSULTAR', 'consultar'), 'consultar')]"
            ))
        )
        boton.click()

        # Esperar resultado
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
        driver.save_screenshot(f"/app/error_dni_{dni}.png")
        resultados.append({
            "DNI": dni,
            "Miembro de Mesa": "ERROR",
            "Ubicación": str(e),
            "Dirección Local": "-"
        })

driver.quit()

salida = pd.DataFrame(resultados)
salida.to_excel("resultados.xlsx", index=False)
print("Proceso terminado. Archivo generado: resultados.xlsx")