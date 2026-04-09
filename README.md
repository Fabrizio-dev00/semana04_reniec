# Verificador de Miembros de Mesa

Aplicación en Python que lee una lista de DNIs desde Excel, consulta la página de la ONPE y genera otro Excel con los resultados.

## Requisitos

Docker instalado
Archivo dnis.xlsx con una columna llamada DNI

## Construir la imagen

'''bash
docker build -t miembro-mesa:v1 .