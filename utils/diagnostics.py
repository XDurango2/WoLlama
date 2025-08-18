import winrm
import json
import subprocess

def agregar_a_trusted_hosts(host):
    """Agrega la IP del host a la lista de TrustedHosts si no está incluida."""
    try:
        # Obtener la lista actual de TrustedHosts
        comando_obtener = ["powershell", "-Command", "(Get-Item WSMan:\\localhost\\Client\\TrustedHosts).Value"]
        resultado = subprocess.run(comando_obtener, capture_output=True, text=True)
        trusted_hosts = resultado.stdout.strip()

        # Verificar si la IP ya está en TrustedHosts
        if host not in trusted_hosts:
            print(f"Agregando {host} a TrustedHosts...")
            comando_agregar = [
                "powershell", "-Command",
                f"Set-Item WSMan:\\localhost\\Client\\TrustedHosts -Value '{trusted_hosts},{host}' -Force"
                if trusted_hosts else
                f"Set-Item WSMan:\\localhost\\Client\\TrustedHosts -Value '{host}' -Force"
            ]
            subprocess.run(comando_agregar, check=True)
            print(f"{host} agregado a TrustedHosts.")
        else:
            print(f"{host} ya está en TrustedHosts.")
    except Exception as e:
        print(f"Error al agregar {host} a TrustedHosts: {e}")

def ejecutar_comando(host, usuario, password, comando):
    """Ejecuta un comando en una máquina remota a través de WinRM y devuelve el resultado."""
    try:
        # Asegurarse de que el host esté en TrustedHosts
        agregar_a_trusted_hosts(host)

        # Crear sesión y ejecutar el comando
        sesion = winrm.Session(f'http://{host}:5985/wsman', auth=(usuario, password))
        resultado = sesion.run_cmd(comando)
        return resultado.std_out.decode().strip()
    except Exception as e:
        return f"Error: {e}"

def obtener_especificaciones(host, usuario, password):
    """Obtiene información detallada del hardware y sistema operativo."""
    especificaciones = {
        "Sistema Operativo": "wmic os get Caption,Version,OSArchitecture",
        "Procesador": "wmic cpu get Name,NumberOfCores,MaxClockSpeed",
        "Memoria RAM": "wmic OS get TotalVisibleMemorySize,FreePhysicalMemory",
        "Discos Duros": "wmic logicaldisk get Caption,Size,FreeSpace",
        "Tarjeta Madre": "wmic baseboard get Manufacturer,Product",
        "Tarjeta de Red": "wmic nic where \"NetEnabled=true\" get Name,MACAddress",
    }
    
    resultados = {}
    for key, cmd in especificaciones.items():
        resultados[key] = ejecutar_comando(host, usuario, password, cmd)

    return resultados

def diagnostico_multiples(hosts, usuario, password):
    """Ejecuta pruebas de diagnóstico y obtiene especificaciones de hardware/software en múltiples máquinas."""
    pruebas = {
        "Procesos Activos": "tasklist",
        "Uso de CPU": "wmic cpu get loadpercentage",
        "Memoria Disponible": "wmic OS get FreePhysicalMemory",
        "Servicios Críticos": "sc query type= service state= all"
    }

    resultados = {}
    for host in hosts:
        print(f"\n--- Diagnóstico y Especificaciones para {host} ---")
        resultados[host] = {}

        # Obtener diagnóstico
        resultados[host]["Diagnóstico"] = {}
        for prueba, comando in pruebas.items():
            comando_final = comando.replace("{host}", host)
            print(f"Ejecutando prueba: {prueba} en {host}...")
            resultados[host]["Diagnóstico"][prueba] = ejecutar_comando(host, usuario, password, comando_final)

        # Obtener especificaciones de la PC
        print(f"Obteniendo especificaciones de {host}...")
        resultados[host]["Especificaciones"] = obtener_especificaciones(host, usuario, password)

    return resultados

if __name__ == "__main__":
    hosts = ["148.231.64.250"]  # Lista de PCs a diagnosticar
    usuario = "FDM-Soporte"
    password = "labder"

    resultados = diagnostico_multiples(hosts, usuario, password)

    # Guardar los resultados en un archivo JSON
    with open("diagnostico_especificaciones.json", "w") as f:
        json.dump(resultados, f, indent=4)

    print("\n✅ Diagnóstico completado. Resultados guardados en 'diagnostico_especificaciones.json'.")
