import openai
import json
import re # Importamos re para expresiones regulares

# --- Configuración ---
# Reemplaza 'TU_API_KEY_AQUI' con tu clave real de OpenAI
openai.api_key = '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'
DATASET_FILE = 'paquetes_turisticos.json' # Asegúrate de que tu archivo JSON se llame así o cambia el nombre aquí

# --- Cargar el dataset ---
def cargar_dataset(ruta_archivo):
    """Carga los datos de los paquetes turísticos desde un archivo JSON."""
    try:
        with open(ruta_archivo, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: El archivo '{ruta_archivo}' no se encontró. Asegúrate de que esté en el mismo directorio.")
        return []
    except json.JSONDecodeError:
        print(f"Error: No se pudo decodificar el archivo JSON '{ruta_archivo}'. Verifica su formato.")
        return []

paquetes_turisticos = cargar_dataset(DATASET_FILE)

# --- Funciones para el chat ---

def extraer_presupuesto(texto):
    """
    Intenta extraer un presupuesto numérico de un texto usando expresiones regulares.
    Prioriza números antes de la palabra "dólares", "soles", "$", o simplemente un número.
    """
    # Patrón para encontrar números con o sin separadores de miles y decimales
    # Que estén cerca de palabras clave como "dólares", "soles", "$" o simplemente un número
    # Buscamos números enteros o decimales, opcionalmente con un signo de dólar o sol delante/detrás
    match = re.search(r'(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?)\s*(?:dolares|soles|\$)?|\$?\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?)', texto, re.IGNORECASE)
    if match:
        # Tomamos el grupo que haya coincidido (el primero que no sea None)
        presupuesto_str = match.group(1) if match.group(1) else match.group(2)
        # Limpiamos el string para convertirlo a float (removiendo comas de miles y convirtiendo puntos a decimales)
        presupuesto_str = presupuesto_str.replace('.', '').replace(',', '.')
        try:
            return float(presupuesto_str)
        except ValueError:
            return None
    return None

def buscar_paquetes_por_presupuesto(presupuesto_maximo):
    """Busca paquetes turísticos que se ajusten a un presupuesto máximo."""
    paquetes_encontrados = []
    if not paquetes_turisticos:
        return []
    for paquete in paquetes_turisticos:
        if paquete.get("precio") is not None and paquete["precio"] <= presupuesto_maximo:
            paquetes_encontrados.append(paquete)
    return paquetes_encontrados

def generar_respuesta_chat(historial_conversacion, mensaje_usuario):
    """
    Genera una respuesta para el chat.
    Primero intenta extraer el presupuesto. Si lo encuentra, usa la lógica personalizada.
    Si no, delega a la API de GPT.
    """
    presupuesto = extraer_presupuesto(mensaje_usuario)

    if presupuesto:
        paquetes_sugeridos = buscar_paquetes_por_presupuesto(presupuesto)
        if paquetes_sugeridos:
            respuesta = f"¡Claro! Con un presupuesto de ${presupuesto:,.2f}, te sugiero los siguientes paquetes:\n\n"
            for p in paquetes_sugeridos:
                lugares_str = ", ".join(p["lugares"])
                respuesta += f"- **{p['nombre']}**: {p['dias']} días, ${p['precio']:,.2f}. Lugares: {lugares_str}.\n"
            respuesta += "\n¿Te gustaría más detalles sobre alguno de ellos o tienes otro presupuesto en mente?"
            return respuesta
        else:
            return f"Lo siento, no encontré paquetes que se ajusten a un presupuesto de ${presupuesto:,.2f}. ¿Te gustaría probar con un presupuesto diferente o buscar por otras características?"
    else:
        # Si no se detecta un presupuesto, se usa la API de GPT para una conversación general
        mensajes_gpt = [{"role": "system", "content": "Eres un asistente amigable especializado en viajes y turismo. Tu objetivo es ayudar a los usuarios a encontrar itinerarios y paquetes turísticos."}]
        mensajes_gpt.extend(historial_conversacion)
        mensajes_gpt.append({"role": "user", "content": mensaje_usuario})

        try:
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo", # Puedes probar con otros modelos si lo deseas, como "gpt-4"
                messages=mensajes_gpt,
                max_tokens=250,
                temperature=0.7
            )
            return response.choices[0].message.content
        except openai.RateLimitError:
            return "He alcanzado el límite de solicitudes. Por favor, intenta de nuevo en un momento."
        except openai.APIError as e:
            return f"Hubo un error con la API de OpenAI: {e}"
        except Exception as e:
            return f"Ocurrió un error inesperado: {e}"

# --- Bucle principal del chat ---
def iniciar_chat():
    """Inicia el bucle de conversación del chat."""
    print("¡Hola! Soy tu asistente de viajes. Estoy aquí para ayudarte a encontrar el itinerario perfecto. ¿Cuál es tu presupuesto o qué tipo de viaje buscas?")
    historial_conversacion = []

    while True:
        mensaje_usuario = input("Tú: ")
        if mensaje_usuario.lower() in ["salir", "adios", "terminar"]:
            print("Asistente: ¡Hasta luego! Espero haberte ayudado en tu búsqueda de viajes.")
            break

        respuesta = generar_respuesta_chat(historial_conversacion, mensaje_usuario)
        print(f"Asistente: {respuesta}")

        # Actualizar el historial de conversación para GPT
        historial_conversacion.append({"role": "user", "content": mensaje_usuario})
        historial_conversacion.append({"role": "assistant", "content": respuesta})

if __name__ == "__main__":
    iniciar_chat()