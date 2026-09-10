import os
import json
from datetime import datetime, date, timedelta
import sys
import calendar
from typing import Dict, List, Optional, Any

DATA_FILE = "agenda_completa.json"

class Agenda:
    def __init__(self):
        self.items = {}
        self.cargar_datos()
        self.actualizar_fechas_proximas()
    
    def cargar_datos(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r', encoding='utf-8') as f:
                    datos = json.load(f)
                    self.items = datos.get('items', {})
                print("📚 Datos cargados exitosamente")
                return True
            except Exception as e:
                print(f"⚠️ Error al cargar los datos: {e}. Creando agenda nueva.")
                self.items = {}
                return False
        return False
    
    def guardar_datos(self):
        try:
            datos = {'items': self.items}
            with open(DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(datos, f, indent=4, ensure_ascii=False)
            print("💾 Datos guardados exitosamente")
            return True
        except Exception as e:
            print(f"❌ Error al guardar: {e}")
            return False
    
    def obtener_frecuencia_dias(self, frecuencia: str) -> int:
        frecuencias = {
            'diaria': 1, 'semanal': 7, 'quincenal': 15, 'mensual': 30,
            'bimestral': 60, 'trimestral': 90, 'cuatrimestral': 120,
            'semestral': 180, 'anual': 365
        }
        return frecuencias.get(frecuencia, 1)
    
    def generar_siguientes_fechas(self, item: Dict, desde: date, hasta: Optional[date] = None) -> List[date]:
        fechas = []
        fecha_actual = desde
        
        if not item.get('repetir'):
            return [desde]
        
        frecuencia = item['frecuencia']
        fecha_fin = item.get('fecha_fin')
        
        if fecha_fin:
            fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
        
        if hasta is None:
            hasta = date.today() + timedelta(days=365)
        
        if item['tipo'] in ['cumpleanos', 'feriado'] and item.get('repetir'):
            while fecha_actual <= hasta:
                if fecha_fin and fecha_actual > fecha_fin:
                    break
                fechas.append(fecha_actual)
                try:
                    fecha_actual = date(fecha_actual.year + 1, fecha_actual.month, fecha_actual.day)
                except ValueError:
                    fecha_actual = date(fecha_actual.year + 1, fecha_actual.month, 
                                      min(fecha_actual.day, calendar.monthrange(fecha_actual.year + 1, fecha_actual.month)[1]))
            return fechas
        
        dias_intervalo = self.obtener_frecuencia_dias(frecuencia)
        
        while fecha_actual <= hasta:
            if fecha_fin and fecha_actual > fecha_fin:
                break
            fechas.append(fecha_actual)
            fecha_actual += timedelta(days=dias_intervalo)
        
        return fechas
    
    def actualizar_fechas_proximas(self):
        hoy = date.today()
        cambios = False
        
        for item_id, item in self.items.items():
            if item.get('repetir', False):
                ultima_fecha_str = item.get('ultima_fecha_generada', item['fecha_inicio'])
                ultima_fecha = datetime.strptime(ultima_fecha_str, '%Y-%m-%d').date()
                
                nuevas_fechas = self.generar_siguientes_fechas(item, ultima_fecha, hoy)
                
                if nuevas_fechas:
                    fechas_str = [f.strftime('%Y-%m-%d') for f in nuevas_fechas]
                    item['fechas_proximas'] = fechas_str
                    item['ultima_fecha_generada'] = fechas_str[-1]
                    cambios = True
        
        if cambios:
            self.guardar_datos()
    
    def inicializar_ocurrencias(self, item_id: str):
        item = self.items.get(item_id)
        if not item or not item.get('repetir', False):
            return
        
        fechas_proximas = item.get('fechas_proximas', [])
        ocurrencias = {}
        
        for fecha in fechas_proximas:
            ocurrencias[fecha] = {
                'completada': False,
                'completada_en': None,
                'notas': ''
            }
        
        item['ocurrencias'] = ocurrencias
    
    def agregar_item(self, tipo, titulo, descripcion, fecha_inicio, repetir=False, 
                     frecuencia=None, fecha_fin=None, prioridad='Media', 
                     lugar='', notas='', edad=None):
        try:
            datetime.strptime(fecha_inicio, '%Y-%m-%d')
            
            nuevo_id = str(max([int(k) for k in self.items.keys()] + [0]) + 1)
            
            item = {
                'tipo': tipo,
                'titulo': titulo,
                'descripcion': descripcion,
                'fecha_inicio': fecha_inicio,
                'repetir': repetir,
                'creado': datetime.now().strftime('%Y-%m-%d %H:%M'),
                'notas': notas,
                'ocurrencias': {}
            }
            
            if repetir:
                item['frecuencia'] = frecuencia
                if fecha_fin:
                    item['fecha_fin'] = fecha_fin
                item['ultima_fecha_generada'] = fecha_inicio
            else:
                if tipo == 'tarea':
                    item['completada'] = False
            
            if tipo == 'tarea':
                item['prioridad'] = prioridad
            elif tipo == 'evento':
                item['lugar'] = lugar
            elif tipo == 'cumpleanos' and edad is not None:
                item['edad'] = edad
            
            self.items[nuevo_id] = item
            self.actualizar_fechas_proximas()
            self.inicializar_ocurrencias(nuevo_id)
            self.guardar_datos()
            
            return True, nuevo_id
        except Exception as e:
            return False, str(e)
    
    def editar_item(self, item_id, titulo, descripcion, fecha_inicio, repetir=False,
                    frecuencia=None, fecha_fin=None, prioridad='Media',
                    lugar='', notas='', edad=None):
        try:
            if item_id not in self.items:
                return False, "Item no encontrado"
            
            datetime.strptime(fecha_inicio, '%Y-%m-%d')
            
            item = self.items[item_id]
            item['titulo'] = titulo
            item['descripcion'] = descripcion
            item['fecha_inicio'] = fecha_inicio
            item['repetir'] = repetir
            item['notas'] = notas
            
            if repetir:
                item['frecuencia'] = frecuencia
                if fecha_fin:
                    item['fecha_fin'] = fecha_fin
                else:
                    item.pop('fecha_fin', None)
                item['ultima_fecha_generada'] = fecha_inicio
            else:
                item.pop('frecuencia', None)
                item.pop('fecha_fin', None)
                item.pop('ultima_fecha_generada', None)
                item.pop('fechas_proximas', None)
                if item['tipo'] == 'tarea':
                    item['completada'] = False
            
            if item['tipo'] == 'tarea':
                item['prioridad'] = prioridad
            elif item['tipo'] == 'evento':
                item['lugar'] = lugar
            elif item['tipo'] == 'cumpleanos' and edad is not None:
                item['edad'] = edad
            
            self.actualizar_fechas_proximas()
            self.inicializar_ocurrencias(item_id)
            self.guardar_datos()
            
            return True, "Item actualizado exitosamente"
        except Exception as e:
            return False, str(e)
    
    def completar_ocurrencia(self, item_id, fecha):
        item = self.items.get(item_id)
        if not item:
            return False, "Item no encontrado"
        
        if not item.get('repetir', False):
            return False, "Esta tarea no es repetitiva"
        
        ocurrencias = item.get('ocurrencias', {})
        if fecha not in ocurrencias:
            return False, "Fecha no encontrada en las ocurrencias"
        
        if ocurrencias[fecha].get('completada', False):
            return False, "Esta ocurrencia ya está completada"
        
        ocurrencias[fecha]['completada'] = True
        ocurrencias[fecha]['completada_en'] = datetime.now().strftime('%Y-%m-%d %H:%M')
        self.guardar_datos()
        return True, "Ocurrencia completada exitosamente"
    
    def completar_tarea_normal(self, item_id):
        item = self.items.get(item_id)
        if not item:
            return False, "Item no encontrado"
        
        if item.get('repetir', False):
            return False, "Esta es una tarea repetitiva, use completar_ocurrencia"
        
        if item.get('completada', False):
            return False, "La tarea ya está completada"
        
        item['completada'] = True
        item['completada_en'] = datetime.now().strftime('%Y-%m-%d %H:%M')
        self.guardar_datos()
        return True, "Tarea completada exitosamente"
    
    def completar_todas_ocurrencias(self, item_id):
        item = self.items.get(item_id)
        if not item:
            return False, "Item no encontrado"
        
        if not item.get('repetir', False):
            return False, "Esta tarea no es repetitiva"
        
        ocurrencias = item.get('ocurrencias', {})
        for fecha in ocurrencias:
            if not ocurrencias[fecha].get('completada', False):
                ocurrencias[fecha]['completada'] = True
                ocurrencias[fecha]['completada_en'] = datetime.now().strftime('%Y-%m-%d %H:%M')
        
        self.guardar_datos()
        return True, "Todas las ocurrencias completadas exitosamente"
    
    def obtener_items(self, tipo=None, solo_pendientes=False):
        items_mostrar = self.items
        
        if tipo:
            items_mostrar = {k: v for k, v in items_mostrar.items() if v['tipo'] == tipo}
        
        if solo_pendientes:
            items_filtrados = {}
            for k, v in items_mostrar.items():
                if v['tipo'] == 'tarea':
                    if not v.get('repetir', False):
                        if not v.get('completada', False):
                            items_filtrados[k] = v
                    else:
                        ocurrencias = v.get('ocurrencias', {})
                        tiene_pendientes = any(not occ.get('completada', False) 
                                             for occ in ocurrencias.values())
                        if tiene_pendientes:
                            items_filtrados[k] = v
            return items_filtrados
        
        return items_mostrar
    
    def obtener_estadisticas(self, item_id):
        item = self.items.get(item_id)
        if not item or item['tipo'] != 'tarea' or not item.get('repetir', False):
            return None
        
        ocurrencias = item.get('ocurrencias', {})
        total = len(ocurrencias)
        completadas = sum(1 for occ in ocurrencias.values() if occ.get('completada', False))
        pendientes = total - completadas
        
        return {
            'total': total,
            'completadas': completadas,
            'pendientes': pendientes,
            'porcentaje': (completadas/total*100) if total > 0 else 0,
            'completadas_list': [(fecha, occ) for fecha, occ in ocurrencias.items() 
                               if occ.get('completada', False)],
            'pendientes_list': [(fecha, occ) for fecha, occ in ocurrencias.items() 
                              if not occ.get('completada', False)]
        }
    
    def eliminar_item(self, item_id):
        if item_id in self.items:
            del self.items[item_id]
            self.guardar_datos()
            return True, "Item eliminado exitosamente"
        return False, "Item no encontrado"
    
    def buscar(self, termino):
        termino = termino.lower()
        resultados = []
        
        for id_item, item in self.items.items():
            if (termino in item['titulo'].lower() or 
                termino in item.get('descripcion', '').lower() or
                termino in item.get('notas', '').lower()):
                resultados.append((id_item, item))
        
        return resultados
    
    def obtener_recordatorios_hoy(self):
        hoy = date.today()
        hoy_str = hoy.strftime('%Y-%m-%d')
        recordatorios = []
        
        for id_item, item in self.items.items():
            if item.get('fechas_proximas') and hoy_str in item['fechas_proximas']:
                if item['tipo'] == 'tarea':
                    ocurrencia = item.get('ocurrencias', {}).get(hoy_str, {})
                    if ocurrencia.get('completada', False):
                        continue
                recordatorios.append((id_item, item))
        
        return recordatorios
    
    def obtener_proximos_dias(self, dias=7):
        hoy = date.today()
        resultados = {}
        
        for i in range(dias + 1):
            fecha = hoy + timedelta(days=i)
            fecha_str = fecha.strftime('%Y-%m-%d')
            resultados[fecha_str] = []
            
            for id_item, item in self.items.items():
                if item.get('fechas_proximas') and fecha_str in item['fechas_proximas']:
                    if item['tipo'] == 'tarea':
                        ocurrencia = item.get('ocurrencias', {}).get(fecha_str, {})
                        if ocurrencia.get('completada', False):
                            continue
                    resultados[fecha_str].append((id_item, item))
        
        return resultados
    
    def exportar_csv(self, tipo, archivo):
        items_tipo = {k: v for k, v in self.items.items() if v['tipo'] == tipo}
        
        if not items_tipo:
            print(f"❌ No hay items de tipo '{tipo}' para exportar")
            return
        
        if not archivo.endswith('.csv'):
            archivo += '.csv'
        
        import csv
        
        with open(archivo, 'w', newline='', encoding='utf-8') as f:
            if tipo == 'tarea':
                fieldnames = ['ID', 'Título', 'Descripción', 'Prioridad', 'Completada', 
                             'Fecha Inicio', 'Repite', 'Frecuencia', 'Notas']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for id_item, item in items_tipo.items():
                    if item.get('repetir', False):
                        ocurrencias = item.get('ocurrencias', {})
                        total = len(ocurrencias)
                        completadas = sum(1 for occ in ocurrencias.values() if occ.get('completada', False))
                        completada = f"{completadas}/{total} ({completadas/total*100:.0f}%)" if total > 0 else "0/0"
                    else:
                        completada = 'Sí' if item.get('completada', False) else 'No'
                    
                    writer.writerow({
                        'ID': id_item,
                        'Título': item['titulo'],
                        'Descripción': item.get('descripcion', ''),
                        'Prioridad': item.get('prioridad', ''),
                        'Completada': completada,
                        'Fecha Inicio': item['fecha_inicio'],
                        'Repite': 'Sí' if item.get('repetir', False) else 'No',
                        'Frecuencia': item.get('frecuencia', ''),
                        'Notas': item.get('notas', '')
                    })
            else:
                fieldnames = ['ID', 'Título', 'Descripción', 'Fecha Inicio', 
                             'Repite', 'Frecuencia', 'Notas']
                if tipo == 'evento':
                    fieldnames.insert(4, 'Lugar')
                elif tipo == 'cumpleanos':
                    fieldnames.insert(4, 'Edad')
                
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for id_item, item in items_tipo.items():
                    row = {
                        'ID': id_item,
                        'Título': item['titulo'],
                        'Descripción': item.get('descripcion', ''),
                        'Fecha Inicio': item['fecha_inicio'],
                        'Repite': 'Sí' if item.get('repetir', False) else 'No',
                        'Frecuencia': item.get('frecuencia', ''),
                        'Notas': item.get('notas', '')
                    }
                    if tipo == 'evento':
                        row['Lugar'] = item.get('lugar', '')
                    elif tipo == 'cumpleanos':
                        row['Edad'] = item.get('edad', '')
                    
                    writer.writerow(row)
        
        print(f"✅ Datos exportados a {archivo}")
    
    def exportar_json_completo(self, archivo):
        if not archivo.endswith('.json'):
            archivo += '.json'
        
        with open(archivo, 'w', encoding='utf-8') as f:
            json.dump(self.items, f, indent=4, ensure_ascii=False)
        
        print(f"✅ Agenda completa exportada a {archivo}")

    def mostrar_menu(self):
        print("\n" + "="*60)
        print("              📚 AGENDA COMPLETA v4.0")
        print("="*60)
        print("📋 ITEMS:")
        print("  1. Agregar item")
        print("  2. Ver todos los items")
        print("  3. Ver tareas")
        print("  4. Ver tareas pendientes")
        print("  5. Ver eventos")
        print("  6. Ver cumpleaños")
        print("  7. Ver feriados")
        print("  8. Editar item")
        print("  9. Marcar tarea como completada")
        print(" 10. Ver estadísticas de tarea")
        print(" 11. Eliminar item")
        print("\n🔍 UTILIDADES:")
        print(" 12. Ver recordatorios de hoy")
        print(" 13. Ver próximos 7 días")
        print(" 14. Buscar en toda la agenda")
        print("\n💾 EXPORTAR:")
        print(" 15. Exportar a CSV")
        print(" 16. Exportar agenda completa a JSON")
        print(" 17. Salir")
        print("-"*60)

    def main_console(self):
        while True:
            self.mostrar_menu()
            opcion = input("\nSelecciona una opción (1-17): ").strip()
            
            if opcion == "1":
                self.agregar_item_console()
            elif opcion == "2":
                self.ver_items_console()
            elif opcion == "3":
                self.ver_tareas_console()
            elif opcion == "4":
                self.ver_tareas_pendientes_console()
            elif opcion == "5":
                self.ver_eventos_console()
            elif opcion == "6":
                self.ver_cumpleanos_console()
            elif opcion == "7":
                self.ver_feriados_console()
            elif opcion == "8":
                self.editar_item_console()
            elif opcion == "9":
                self.completar_tarea_console()
            elif opcion == "10":
                self.ver_estadisticas_console()
            elif opcion == "11":
                self.eliminar_item_console()
            elif opcion == "12":
                self.recordatorios_hoy_console()
            elif opcion == "13":
                self.proximos_dias_console()
            elif opcion == "14":
                self.buscar_console()
            elif opcion == "15":
                self.exportar_csv_console()
            elif opcion == "16":
                self.exportar_json_console()
            elif opcion == "17":
                print("\n👋 ¡Hasta pronto!")
                self.guardar_datos()
                sys.exit(0)
            else:
                print("❌ Opción no válida")
            
            input("\nPresiona Enter para continuar...")

    def agregar_item_console(self):
        print("\n➕ NUEVO ITEM")
        print("\nTipo de item:")
        print("  1. Tarea")
        print("  2. Evento")
        print("  3. Cumpleaños")
        print("  4. Feriado")
        tipo_opcion = input("Selecciona tipo (1-4): ").strip()
        
        tipos = {'1': 'tarea', '2': 'evento', '3': 'cumpleanos', '4': 'feriado'}
        tipo = tipos.get(tipo_opcion)
        if not tipo:
            print("❌ Opción no válida")
            return
        
        titulo = input("Título/Nombre: ").strip()
        if not titulo:
            print("❌ El título no puede estar vacío")
            return
        
        descripcion = input("Descripción (opcional): ").strip()
        fecha_inicio = input("Fecha de inicio (YYYY-MM-DD) [hoy]: ").strip()
        if not fecha_inicio:
            fecha_inicio = date.today().strftime('%Y-%m-%d')
        
        try:
            datetime.strptime(fecha_inicio, '%Y-%m-%d')
        except:
            print("❌ Formato de fecha inválido")
            return
        
        repetir = False
        frecuencia = None
        fecha_fin = None
        edad = None
        
        if tipo in ['tarea', 'evento']:
            print("\n¿El item se repite?")
            repetir = input("  (s/n): ").lower() == 's'
            
            if repetir:
                print("\nFrecuencias disponibles:")
                print("  1. Diaria")
                print("  2. Semanal")
                print("  3. Quincenal")
                print("  4. Mensual")
                print("  5. Bimestral")
                print("  6. Trimestral")
                print("  7. Cuatrimestral")
                print("  8. Semestral")
                print("  9. Anual")
                freq_opcion = input("Selecciona frecuencia (1-9): ").strip()
                
                frecuencias = {
                    '1': 'diaria', '2': 'semanal', '3': 'quincenal',
                    '4': 'mensual', '5': 'bimestral', '6': 'trimestral',
                    '7': 'cuatrimestral', '8': 'semestral', '9': 'anual'
                }
                frecuencia = frecuencias.get(freq_opcion)
                
                if not frecuencia:
                    print("❌ Opción no válida")
                    return
                
                fecha_fin = input("Fecha de fin (YYYY-MM-DD, opcional): ").strip()
                if fecha_fin:
                    try:
                        datetime.strptime(fecha_fin, '%Y-%m-%d')
                    except:
                        print("❌ Formato de fecha inválido")
                        return
        elif tipo == 'cumpleanos':
            repetir = True
            frecuencia = 'anual'
            fecha_nac = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
            hoy = date.today()
            edad = hoy.year - fecha_nac.year
            if hoy.month < fecha_nac.month or (hoy.month == fecha_nac.month and hoy.day < fecha_nac.day):
                edad -= 1
        elif tipo == 'feriado':
            print("\n¿El feriado se repite cada año?")
            repetir = input("  (s/n): ").lower() == 's'
            if repetir:
                frecuencia = 'anual'
        
        if tipo == 'tarea':
            prioridad = input("Prioridad (Alta/Media/Baja) [Media]: ").strip() or "Media"
        else:
            prioridad = 'Media'
        
        if tipo == 'evento':
            lugar = input("Lugar (opcional): ").strip()
        else:
            lugar = ''
        
        notas = input("Notas adicionales (opcional): ").strip()
        
        success, result = self.agregar_item(
            tipo, titulo, descripcion, fecha_inicio,
            repetir, frecuencia, fecha_fin, prioridad, lugar, notas, edad
        )
        
        if success:
            print(f"✅ Item creado con ID: {result}")
        else:
            print(f"❌ Error al crear: {result}")

    def editar_item_console(self):
        self.ver_items_console()
        if not self.items:
            return
        
        item_id = input("\nID del item a editar: ").strip()
        if item_id not in self.items:
            print("❌ ID no válido")
            return
        
        item = self.items[item_id]
        print(f"\n✏️ EDITANDO: {item['titulo']}")
        
        titulo = input(f"Título [{item['titulo']}]: ").strip() or item['titulo']
        descripcion = input(f"Descripción [{item.get('descripcion', '')}]: ").strip() or item.get('descripcion', '')
        fecha_inicio = input(f"Fecha inicio [{item['fecha_inicio']}]: ").strip() or item['fecha_inicio']
        
        try:
            datetime.strptime(fecha_inicio, '%Y-%m-%d')
        except:
            print("❌ Formato de fecha inválido")
            return
        
        if item['tipo'] in ['tarea', 'evento']:
            repetir_str = input(f"¿Repetir? (s/n) [{ 's' if item.get('repetir') else 'n' }]: ").strip().lower()
            repetir = repetir_str == 's' if repetir_str else item.get('repetir', False)
            
            if repetir:
                print("\nFrecuencias disponibles:")
                print("  1. Diaria  2. Semanal  3. Quincenal  4. Mensual")
                print("  5. Bimestral  6. Trimestral  7. Cuatrimestral")
                print("  8. Semestral  9. Anual")
                freq_opcion = input(f"Frecuencia [{item.get('frecuencia', 'mensual')}]: ").strip()
                
                frecuencias = {
                    '1': 'diaria', '2': 'semanal', '3': 'quincenal',
                    '4': 'mensual', '5': 'bimestral', '6': 'trimestral',
                    '7': 'cuatrimestral', '8': 'semestral', '9': 'anual'
                }
                if freq_opcion:
                    frecuencia = frecuencias.get(freq_opcion)
                    if not frecuencia:
                        print("❌ Opción no válida")
                        return
                else:
                    frecuencia = item.get('frecuencia', 'mensual')
                
                fecha_fin = input(f"Fecha fin [{item.get('fecha_fin', '')}]: ").strip() or item.get('fecha_fin', None)
                if fecha_fin:
                    try:
                        datetime.strptime(fecha_fin, '%Y-%m-%d')
                    except:
                        print("❌ Formato de fecha inválido")
                        return
            else:
                frecuencia = None
                fecha_fin = None
        else:
            repetir = item.get('repetir', False)
            frecuencia = item.get('frecuencia', None)
            fecha_fin = item.get('fecha_fin', None)
        
        if item['tipo'] == 'tarea':
            prioridad = input(f"Prioridad [{item.get('prioridad', 'Media')}]: ").strip() or item.get('prioridad', 'Media')
        else:
            prioridad = item.get('prioridad', 'Media')
        
        if item['tipo'] == 'evento':
            lugar = input(f"Lugar [{item.get('lugar', '')}]: ").strip() or item.get('lugar', '')
        else:
            lugar = item.get('lugar', '')
        
        notas = input(f"Notas [{item.get('notas', '')}]: ").strip() or item.get('notas', '')
        
        edad = None
        if item['tipo'] == 'cumpleanos':
            fecha_nac = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
            hoy = date.today()
            edad = hoy.year - fecha_nac.year
            if hoy.month < fecha_nac.month or (hoy.month == fecha_nac.month and hoy.day < fecha_nac.day):
                edad -= 1
        
        success, result = self.editar_item(
            item_id, titulo, descripcion, fecha_inicio,
            repetir, frecuencia, fecha_fin, prioridad, lugar, notas, edad
        )
        
        if success:
            print(f"✅ {result}")
        else:
            print(f"❌ {result}")

    def ver_items_console(self):
        items = self.obtener_items()
        if not items:
            print("📭 No hay items")
            return
        
        print("\n" + "="*120)
        print(f"{'ID':<4} {'Tipo':<15} {'Título':<25} {'Fechas':<30} {'Estado':<15} {'Progreso':<20}")
        print("="*120)
        
        for item_id in sorted(items.keys(), key=lambda x: int(x)):
            item = items[item_id]
            titulo = item['titulo'][:24] + "..." if len(item['titulo']) > 24 else item['titulo']
            
            if item.get('repetir', False) and item.get('fechas_proximas'):
                fechas = item['fechas_proximas'][:3]
                fechas_str = ", ".join(fechas)
                if len(item['fechas_proximas']) > 3:
                    fechas_str += f"... (+{len(item['fechas_proximas'])-3} más)"
            else:
                fechas_str = item['fecha_inicio']
            
            emojis = {'tarea': '📋', 'evento': '📅', 'cumpleanos': '🎂', 'feriado': '🎉'}
            tipo_str = f"{emojis.get(item['tipo'], '📌')} {item['tipo']}"
            if item.get('repetir', False):
                tipo_str += f" ({item['frecuencia']})"
            
            if item['tipo'] == 'tarea':
                if item.get('repetir', False):
                    ocurrencias = item.get('ocurrencias', {})
                    total = len(ocurrencias)
                    completadas = sum(1 for occ in ocurrencias.values() if occ.get('completada', False))
                    if total > 0:
                        progreso = f"{completadas}/{total} ({completadas/total*100:.0f}%)"
                        estado = "Todo completado" if completadas == total else "Parcial" if completadas > 0 else "Pendiente"
                    else:
                        progreso = "0/0"
                        estado = "Sin ocurrencias"
                else:
                    estado = "Completada" if item.get('completada', False) else "Pendiente"
                    progreso = "100%" if item.get('completada', False) else "0%"
            else:
                estado = "Activo"
                progreso = "-"
                if item.get('repetir', False):
                    estado += " (repetitivo)"
            
            print(f"{item_id:<4} {tipo_str:<15} {titulo:<25} {fechas_str:<30} {estado:<15} {progreso:<20}")

    def ver_tareas_console(self):
        items = self.obtener_items('tarea')
        if not items:
            print("📭 No hay tareas")
            return
        self._imprimir_items_console(items, "TAREAS")

    def ver_tareas_pendientes_console(self):
        items = self.obtener_items('tarea', True)
        if not items:
            print("🎉 No hay tareas pendientes")
            return
        self._imprimir_items_console(items, "TAREAS PENDIENTES")

    def ver_eventos_console(self):
        items = self.obtener_items('evento')
        if not items:
            print("📭 No hay eventos")
            return
        self._imprimir_items_console(items, "EVENTOS")

    def ver_cumpleanos_console(self):
        items = self.obtener_items('cumpleanos')
        if not items:
            print("📭 No hay cumpleaños")
            return
        self._imprimir_items_console(items, "CUMPLEAÑOS")

    def ver_feriados_console(self):
        items = self.obtener_items('feriado')
        if not items:
            print("📭 No hay feriados")
            return
        self._imprimir_items_console(items, "FERIADOS")

    def _imprimir_items_console(self, items, titulo):
        print(f"\n📋 {titulo}")
        print("="*100)
        for item_id in sorted(items.keys(), key=lambda x: int(x)):
            item = items[item_id]
            print(f"ID: {item_id} | {item['titulo']} | {item['fecha_inicio']}")

    def completar_tarea_console(self):
        self.ver_tareas_pendientes_console()
        items = self.obtener_items('tarea', True)
        if not items:
            return
        
        item_id = input("\nID de la tarea a completar: ").strip()
        if item_id not in items:
            print("❌ ID no válido")
            return
        
        item = items[item_id]
        if not item.get('repetir', False):
            success, msg = self.completar_tarea_normal(item_id)
            print(f"✅ {msg}" if success else f"❌ {msg}")
        else:
            ocurrencias = item.get('ocurrencias', {})
            pendientes = [fecha for fecha, occ in ocurrencias.items() if not occ.get('completada', False)]
            
            if not pendientes:
                print("🎉 No hay ocurrencias pendientes")
                return
            
            print("\nOcurrencias pendientes:")
            for i, fecha in enumerate(sorted(pendientes), 1):
                print(f"  {i}. {fecha}")
            
            print("\nOpciones:")
            print("  1. Completar una ocurrencia específica")
            print("  2. Completar todas las ocurrencias")
            print("  3. Cancelar")
            
            opcion = input("Selecciona (1-3): ").strip()
            
            if opcion == "3":
                return
            elif opcion == "2":
                success, msg = self.completar_todas_ocurrencias(item_id)
                print(f"✅ {msg}" if success else f"❌ {msg}")
            elif opcion == "1":
                try:
                    idx = int(input("Número de la ocurrencia: ").strip())
                    if 1 <= idx <= len(pendientes):
                        fecha = sorted(pendientes)[idx - 1]
                        success, msg = self.completar_ocurrencia(item_id, fecha)
                        print(f"✅ {msg}" if success else f"❌ {msg}")
                    else:
                        print("❌ Número no válido")
                except ValueError:
                    print("❌ Entrada no válida")

    def ver_estadisticas_console(self):
        repetitivas = {k: v for k, v in self.items.items() 
                      if v['tipo'] == 'tarea' and v.get('repetir', False)}
        
        if not repetitivas:
            print("No hay tareas repetitivas")
            return
        
        print("\nTareas repetitivas:")
        for item_id in sorted(repetitivas.keys(), key=lambda x: int(x)):
            item = repetitivas[item_id]
            print(f"  [{item_id}] {item['titulo']}")
        
        item_id = input("\nID de la tarea: ").strip()
        stats = self.obtener_estadisticas(item_id)
        
        if not stats:
            print("No hay estadísticas disponibles")
            return
        
        item = self.items[item_id]
        print(f"\n📊 ESTADÍSTICAS DE: {item['titulo']}")
        print(f"Total: {stats['total']}")
        print(f"Completadas: {stats['completadas']} ({stats['porcentaje']:.1f}%)")
        print(f"Pendientes: {stats['pendientes']}")
        
        if stats['completadas'] > 0:
            print("\n✅ Completadas:")
            for fecha, occ in sorted(stats['completadas_list']):
                print(f"  {fecha} - {occ.get('completada_en', 'N/A')}")
        
        if stats['pendientes'] > 0:
            print("\n⏳ Pendientes:")
            for fecha, _ in sorted(stats['pendientes_list']):
                print(f"  {fecha}")

    def eliminar_item_console(self):
        self.ver_items_console()
        if not self.items:
            return
        
        item_id = input("\nID del item a eliminar: ").strip()
        if item_id not in self.items:
            print("❌ ID no válido")
            return
        
        item = self.items[item_id]
        confirmacion = input(f"¿Eliminar '{item['titulo']}'? (s/n): ").lower()
        if confirmacion == 's':
            success, msg = self.eliminar_item(item_id)
            print(f"✅ {msg}" if success else f"❌ {msg}")

    def recordatorios_hoy_console(self):
        recordatorios = self.obtener_recordatorios_hoy()
        
        if not recordatorios:
            print("📭 No hay nada programado para hoy")
            return
        
        print("\n📆 RECORDATORIOS PARA HOY")
        print("="*40)
        for id_item, item in recordatorios:
            emojis = {'tarea': '⏰', 'evento': '📅', 'cumpleanos': '🎂', 'feriado': '🎉'}
            print(f"{emojis.get(item['tipo'], '📌')} {item['titulo']}")
            if item['tipo'] == 'evento' and item.get('lugar'):
                print(f"  Lugar: {item['lugar']}")
            if item['tipo'] == 'cumpleanos':
                print(f"  Edad: {item.get('edad', '?')} años")
            print()

    def proximos_dias_console(self):
        proximos = self.obtener_proximos_dias(7)
        
        print("\n📅 PRÓXIMOS 7 DÍAS")
        print("="*40)
        
        hay_items = False
        for fecha_str in sorted(proximos.keys()):
            if proximos[fecha_str]:
                fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
                print(f"\n{fecha.strftime('%A %d/%m/%Y').upper()}:")
                for id_item, item in proximos[fecha_str]:
                    emojis = {'tarea': '⏰', 'evento': '📅', 'cumpleanos': '🎂', 'feriado': '🎉'}
                    print(f"  {emojis.get(item['tipo'], '📌')} {item['titulo']}")
                hay_items = True
        
        if not hay_items:
            print("No hay nada programado para los próximos 7 días")

    def buscar_console(self):
        termino = input("Término a buscar: ").strip()
        if not termino:
            return
        
        resultados = self.buscar(termino)
        
        if resultados:
            print(f"\n📌 Resultados ({len(resultados)}):")
            for id_item, item in resultados:
                emojis = {'tarea': '📋', 'evento': '📅', 'cumpleanos': '🎂', 'feriado': '🎉'}
                print(f"  {emojis.get(item['tipo'], '📌')} [{id_item}] {item['titulo']}")
        else:
            print("❌ No se encontraron resultados")

    def exportar_csv_console(self):
        print("\n📤 EXPORTAR A CSV")
        print("Tipos disponibles: tarea, evento, cumpleanos, feriado")
        tipo = input("Tipo a exportar: ").strip().lower()
        archivo = input("Nombre del archivo: ").strip()
        self.exportar_csv(tipo, archivo)

    def exportar_json_console(self):
        archivo = input("Nombre del archivo JSON: ").strip()
        self.exportar_json_completo(archivo)


if __name__ == "__main__":
    try:
        agenda = Agenda()
        agenda.main_console()
    except KeyboardInterrupt:
        print("\n\n👋 ¡Hasta pronto!")
        sys.exit(0)