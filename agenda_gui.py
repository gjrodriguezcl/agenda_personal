import os
import json
from datetime import datetime, date, timedelta
import sys
import calendar
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
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
                print(f"IDs disponibles: {list(self.items.keys())}")
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


class AgendaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("📚 Agenda Completa")
        self.root.geometry("1200x800")
        self.root.minsize(800, 600)
        self.root.resizable(True, True)
        
        self.agenda = Agenda()
        self.item_id_actual = None
        
        self.estilo = ttk.Style()
        self.estilo.theme_use('clam')
        
        self.crear_menu()
        self.crear_widgets()
        self.actualizar_lista()
    
    def crear_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        archivo_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Archivo", menu=archivo_menu)
        archivo_menu.add_command(label="Exportar a CSV", command=self.exportar_csv)
        archivo_menu.add_command(label="Exportar a JSON", command=self.exportar_json)
        archivo_menu.add_separator()
        archivo_menu.add_command(label="Salir", command=self.root.quit)
        
        tareas_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tareas", menu=tareas_menu)
        tareas_menu.add_command(label="Nueva Tarea", command=self.nueva_tarea)
        tareas_menu.add_command(label="Nuevo Evento", command=self.nuevo_evento)
        tareas_menu.add_command(label="Nuevo Cumpleaños", command=self.nuevo_cumpleanos)
        tareas_menu.add_command(label="Nuevo Feriado", command=self.nuevo_feriado)
        tareas_menu.add_separator()
        tareas_menu.add_command(label="Editar Item", command=self.editar_item)
        tareas_menu.add_command(label="Marcar como Completada", command=self.completar_tarea)
        
        ver_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Ver", menu=ver_menu)
        ver_menu.add_command(label="Todas las Tareas", command=lambda: self.filtrar_por_tipo(None))
        ver_menu.add_command(label="Solo Tareas", command=lambda: self.filtrar_por_tipo('tarea'))
        ver_menu.add_command(label="Solo Eventos", command=lambda: self.filtrar_por_tipo('evento'))
        ver_menu.add_command(label="Solo Cumpleaños", command=lambda: self.filtrar_por_tipo('cumpleanos'))
        ver_menu.add_command(label="Solo Feriados", command=lambda: self.filtrar_por_tipo('feriado'))
        ver_menu.add_separator()
        ver_menu.add_command(label="Pendientes", command=lambda: self.filtrar_pendientes(True))
        ver_menu.add_command(label="Todas", command=lambda: self.filtrar_pendientes(False))
        
        ayuda_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Ayuda", menu=ayuda_menu)
        ayuda_menu.add_command(label="Acerca de", command=self.acerca_de)
    
    def crear_widgets(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.X, pady=(0, 10))
        
        search_frame = ttk.Frame(top_frame)
        search_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Label(search_frame, text="🔍 Buscar:").pack(side=tk.LEFT, padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_var.trace_add('write', lambda *args: self.buscar())
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        filter_frame = ttk.Frame(top_frame)
        filter_frame.pack(side=tk.RIGHT, padx=(10, 0))
        
        self.filter_var = tk.StringVar(value="todos")
        filters = [("Todos", "todos"), ("Tareas", "tarea"), ("Eventos", "evento"), 
                  ("Cumpleaños", "cumpleanos"), ("Feriados", "feriado")]
        
        for i, (text, value) in enumerate(filters):
            ttk.Radiobutton(filter_frame, text=text, variable=self.filter_var, 
                           value=value, command=self.actualizar_lista).pack(side=tk.LEFT, padx=3)
        
        self.pendientes_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(filter_frame, text="Solo pendientes", 
                       variable=self.pendientes_var, command=self.actualizar_lista).pack(side=tk.LEFT, padx=10)
        
        tree_frame = ttk.Frame(main_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.tree = ttk.Treeview(tree_frame, columns=('ID', 'Tipo', 'Título', 'Descripción', 'Fechas', 'Estado', 'Progreso'), 
                                show='headings', height=12)
        
        self.tree.heading('ID', text='ID')
        self.tree.heading('Tipo', text='Tipo')
        self.tree.heading('Título', text='Título')
        self.tree.heading('Descripción', text='Descripción')
        self.tree.heading('Fechas', text='Fechas próximas')
        self.tree.heading('Estado', text='Estado')
        self.tree.heading('Progreso', text='Progreso')
        
        self.tree.column('ID', width=50, minwidth=40)
        self.tree.column('Tipo', width=150, minwidth=100)
        self.tree.column('Título', width=180, minwidth=120)
        self.tree.column('Descripción', width=200, minwidth=100)
        self.tree.column('Fechas', width=250, minwidth=150)
        self.tree.column('Estado', width=130, minwidth=100)
        self.tree.column('Progreso', width=130, minwidth=100)
        
        vsb = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        vsb.grid(row=0, column=1, sticky=(tk.N, tk.S))
        hsb.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)
        
        self.tree.bind('<<TreeviewSelect>>', self.on_select)
        
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill=tk.X, pady=(0, 0))
        
        action_header_frame = ttk.Frame(bottom_frame)
        action_header_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(action_header_frame, text="📋 Detalles", font=('Arial', 12, 'bold')).pack(side=tk.LEFT)
        
        button_frame = ttk.Frame(action_header_frame)
        button_frame.pack(side=tk.RIGHT)
        
        ttk.Button(button_frame, text="✏️ Editar", command=self.editar_item).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="✅ Completar", command=self.completar_tarea).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="📊 Estadísticas", command=self.ver_estadisticas).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="🗑️ Eliminar", command=self.eliminar_item).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="🔄 Actualizar", command=self.actualizar_lista).pack(side=tk.LEFT, padx=2)
        
        detail_frame = ttk.Frame(bottom_frame)
        detail_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.detail_text = scrolledtext.ScrolledText(detail_frame, wrap=tk.WORD, height=8, font=('Arial', 10))
        self.detail_text.pack(fill=tk.X)
        
        reminder_frame = ttk.Frame(bottom_frame)
        reminder_frame.pack(fill=tk.X)
        
        ttk.Button(reminder_frame, text="📆 Hoy", command=self.ver_hoy).pack(side=tk.LEFT, padx=2)
        ttk.Button(reminder_frame, text="📅 Próximos 7 días", command=self.ver_proximos_dias).pack(side=tk.LEFT, padx=2)
        ttk.Label(reminder_frame, text="💡 Selecciona un item para ver sus detalles").pack(side=tk.RIGHT, padx=5)
    
    def actualizar_lista(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        tipo = self.filter_var.get()
        if tipo == "todos":
            tipo = None
        
        items = self.agenda.obtener_items(tipo, self.pendientes_var.get())
        
        for item_id in sorted(items.keys(), key=lambda x: int(x)):
            item = items[item_id]
            
            titulo = item['titulo'][:25] + "..." if len(item['titulo']) > 25 else item['titulo']
            desc = item.get('descripcion', '')[:20] + "..." if len(item.get('descripcion', '')) > 20 else item.get('descripcion', '')
            
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
                        if completadas == total:
                            estado = "✅ Todo completado"
                        elif completadas > 0:
                            estado = "⏳ Parcial"
                        else:
                            estado = "⏳ Pendiente"
                    else:
                        progreso = "0/0"
                        estado = "📌 Sin ocurrencias"
                else:
                    estado = "✅" if item.get('completada', False) else "⏳"
                    progreso = "100%" if item.get('completada', False) else "0%"
            else:
                estado = "📌"
                progreso = "-"
                if item.get('repetir', False):
                    estado += " 🔄"
            
            self.tree.insert('', tk.END, values=(item_id, tipo_str, titulo, desc, fechas_str, estado, progreso))
    
    def on_select(self, event):
        selection = self.tree.selection()
        if not selection:
            self.detail_text.delete(1.0, tk.END)
            self.item_id_actual = None
            return
        
        # Obtener el item seleccionado
        item_selected = self.tree.item(selection[0])
        values = item_selected['values']
        
        if values and len(values) > 0:
            # Obtener el ID como string y limpiar espacios
            id_seleccionado = str(values[0]).strip()
            
            # Debug: imprimir para verificar
            print(f"ID seleccionado: '{id_seleccionado}'")
            print(f"Keys disponibles: {list(self.agenda.items.keys())}")
            
            # Buscar el item en el diccionario
            item = None
            
            # Intentar 1: Búsqueda directa
            if id_seleccionado in self.agenda.items:
                item = self.agenda.items[id_seleccionado]
                self.item_id_actual = id_seleccionado
                print(f"✅ Encontrado directamente con ID: {id_seleccionado}")
            
            # Intentar 2: Si no se encuentra, intentar como entero (por si hay diferencia de tipo)
            if item is None:
                try:
                    id_int = int(id_seleccionado)
                    id_str = str(id_int)
                    if id_str in self.agenda.items:
                        item = self.agenda.items[id_str]
                        self.item_id_actual = id_str
                        print(f"✅ Encontrado convirtiendo a entero: {id_str}")
                except ValueError:
                    pass
            
            # Intentar 3: Si aún no se encuentra, buscar por coincidencia parcial
            if item is None:
                for key in self.agenda.items.keys():
                    if key.strip() == id_seleccionado.strip():
                        item = self.agenda.items[key]
                        self.item_id_actual = key
                        print(f"✅ Encontrado por coincidencia exacta: {key}")
                        break
            
            # Si no se encuentra, mostrar error
            if item is None:
                self.detail_text.delete(1.0, tk.END)
                self.detail_text.insert(1.0, f"❌ Error: Item con ID '{id_seleccionado}' no encontrado\n\n"
                                           f"IDs disponibles: {', '.join(sorted(self.agenda.items.keys(), key=lambda x: int(x)))}")
                self.item_id_actual = None
                return
            
            # Mostrar los detalles
            self.detail_text.delete(1.0, tk.END)
            
            detalles = f"📌 ID: {self.item_id_actual}\n"
            detalles += f"📂 Tipo: {item['tipo'].capitalize()}\n"
            detalles += f"📝 Título: {item['titulo']}\n"
            detalles += f"📄 Descripción: {item.get('descripcion', 'Sin descripción')}\n"
            detalles += f"📅 Fecha inicio: {item['fecha_inicio']}\n"
            detalles += f"🔄 Repetir: {'Sí' if item.get('repetir', False) else 'No'}\n"
            
            if item.get('repetir', False):
                detalles += f"📊 Frecuencia: {item.get('frecuencia', 'N/A')}\n"
                if item.get('fecha_fin'):
                    detalles += f"📆 Fecha fin: {item['fecha_fin']}\n"
                if item.get('fechas_proximas'):
                    detalles += f"📅 Próximas fechas: {', '.join(item['fechas_proximas'][:5])}\n"
                    if len(item['fechas_proximas']) > 5:
                        detalles += f"   ... y {len(item['fechas_proximas'])-5} más\n"
            
            if item['tipo'] == 'tarea':
                detalles += f"⚡ Prioridad: {item.get('prioridad', 'Media')}\n"
                if item.get('repetir', False):
                    ocurrencias = item.get('ocurrencias', {})
                    total = len(ocurrencias)
                    completadas = sum(1 for occ in ocurrencias.values() if occ.get('completada', False))
                    if total > 0:
                        detalles += f"📊 Progreso: {completadas}/{total} completadas ({completadas/total*100:.0f}%)\n"
                    else:
                        detalles += f"📊 Progreso: 0/0 (Sin ocurrencias)\n"
                else:
                    detalles += f"✅ Completada: {'Sí' if item.get('completada', False) else 'No'}\n"
                    if item.get('completada_en'):
                        detalles += f"🕐 Completada en: {item['completada_en']}\n"
            
            if item['tipo'] == 'evento':
                detalles += f"📍 Lugar: {item.get('lugar', 'Sin especificar')}\n"
            
            if item['tipo'] == 'cumpleanos':
                detalles += f"🎂 Edad: {item.get('edad', 'N/A')} años\n"
            
            if item.get('notas'):
                detalles += f"📝 Notas: {item['notas']}\n"
            else:
                detalles += f"📝 Notas: Sin notas\n"
            
            detalles += f"🕐 Creado: {item.get('creado', 'N/A')}"
            
            self.detail_text.insert(1.0, detalles)
    
    def filtrar_por_tipo(self, tipo):
        self.filter_var.set(tipo if tipo else "todos")
        self.actualizar_lista()
    
    def filtrar_pendientes(self, pendientes):
        self.pendientes_var.set(pendientes)
        self.actualizar_lista()
    
    def buscar(self):
        termino = self.search_var.get().strip()
        if not termino:
            self.actualizar_lista()
            return
        
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        resultados = self.agenda.buscar(termino)
        
        for item_id, item in resultados:
            titulo = item['titulo'][:25] + "..." if len(item['titulo']) > 25 else item['titulo']
            desc = item.get('descripcion', '')[:20] + "..." if len(item.get('descripcion', '')) > 20 else item.get('descripcion', '')
            emojis = {'tarea': '📋', 'evento': '📅', 'cumpleanos': '🎂', 'feriado': '🎉'}
            tipo_str = f"{emojis.get(item['tipo'], '📌')} {item['tipo']}"
            
            self.tree.insert('', tk.END, values=(item_id, tipo_str, titulo, desc, item['fecha_inicio'], "", ""))
    
    def nueva_tarea(self):
        self.dialogo_item('tarea')
    
    def nuevo_evento(self):
        self.dialogo_item('evento')
    
    def nuevo_cumpleanos(self):
        self.dialogo_item('cumpleanos')
    
    def nuevo_feriado(self):
        self.dialogo_item('feriado')
    
    def editar_item(self):
        if self.item_id_actual is None:
            messagebox.showwarning("Advertencia", "Selecciona un item para editar")
            return
        
        item = self.agenda.items.get(self.item_id_actual)
        if not item:
            messagebox.showerror("Error", f"Item con ID {self.item_id_actual} no encontrado")
            self.item_id_actual = None
            return
        
        self.dialogo_editar(self.item_id_actual)
    
    def dialogo_editar(self, item_id):
        item = self.agenda.items.get(item_id)
        if not item:
            messagebox.showerror("Error", "Item no encontrado")
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Editar {item['tipo'].capitalize()}")
        dialog.geometry("650x750")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)
        
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")
        
        canvas = tk.Canvas(dialog)
        scrollbar = ttk.Scrollbar(dialog, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        main_frame = ttk.Frame(scrollable_frame, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_frame, text=f"✏️ Editando {item['tipo'].capitalize()} - ID: {item_id}", 
                 font=('Arial', 14, 'bold')).grid(row=0, column=0, columnspan=2, pady=10)
        
        ttk.Label(main_frame, text="Título/Nombre:*").grid(row=1, column=0, sticky=tk.W, pady=5)
        titulo_entry = ttk.Entry(main_frame, width=50)
        titulo_entry.insert(0, item['titulo'])
        titulo_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(main_frame, text="Descripción:").grid(row=2, column=0, sticky=tk.W, pady=5)
        desc_entry = ttk.Entry(main_frame, width=50)
        desc_entry.insert(0, item.get('descripcion', ''))
        desc_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(main_frame, text="Fecha inicio (YYYY-MM-DD):*").grid(row=3, column=0, sticky=tk.W, pady=5)
        fecha_entry = ttk.Entry(main_frame, width=50)
        fecha_entry.insert(0, item['fecha_inicio'])
        fecha_entry.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=5)
        
        repetir_var = tk.BooleanVar(value=item.get('repetir', False))
        frecuencia_var = tk.StringVar(value=item.get('frecuencia', 'mensual'))
        
        if item['tipo'] in ['tarea', 'evento']:
            ttk.Label(main_frame, text="¿Repetir?").grid(row=4, column=0, sticky=tk.W, pady=5)
            chk_repetir = ttk.Checkbutton(main_frame, variable=repetir_var)
            chk_repetir.grid(row=4, column=1, sticky=tk.W, pady=5)
            
            repetir_frame = ttk.LabelFrame(main_frame, text="Opciones de repetición", padding="10")
            repetir_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
            
            ttk.Label(repetir_frame, text="Frecuencia:").grid(row=0, column=0, sticky=tk.W, pady=5)
            frecuencias = ['diaria', 'semanal', 'quincenal', 'mensual', 'bimestral', 
                          'trimestral', 'cuatrimestral', 'semestral', 'anual']
            frecuencia_combo = ttk.Combobox(repetir_frame, textvariable=frecuencia_var, 
                                           values=frecuencias, state='readonly', width=30)
            frecuencia_combo.grid(row=0, column=1, sticky=tk.W, pady=5)
            
            ttk.Label(repetir_frame, text="Fecha fin (opcional):").grid(row=1, column=0, sticky=tk.W, pady=5)
            fecha_fin_entry = ttk.Entry(repetir_frame, width=30)
            fecha_fin_entry.insert(0, item.get('fecha_fin', ''))
            fecha_fin_entry.grid(row=1, column=1, sticky=tk.W, pady=5)
            
            def toggle_repetir():
                if repetir_var.get():
                    frecuencia_combo.config(state='readonly')
                    fecha_fin_entry.config(state='normal')
                else:
                    frecuencia_combo.config(state='disabled')
                    fecha_fin_entry.config(state='disabled')
            
            repetir_var.trace('w', lambda *args: toggle_repetir())
            toggle_repetir()
        else:
            if item.get('repetir', False):
                ttk.Label(main_frame, text="Repetición:").grid(row=4, column=0, sticky=tk.W, pady=5)
                ttk.Label(main_frame, text=f"✅ {item.get('frecuencia', 'anual')}").grid(row=4, column=1, sticky=tk.W, pady=5)
        
        row_offset = 6 if item['tipo'] in ['tarea', 'evento'] else 5
        
        if item['tipo'] == 'tarea':
            ttk.Label(main_frame, text="Prioridad:").grid(row=row_offset, column=0, sticky=tk.W, pady=5)
            prioridad_var = tk.StringVar(value=item.get('prioridad', 'Media'))
            prioridad_combo = ttk.Combobox(main_frame, textvariable=prioridad_var, 
                                          values=['Alta', 'Media', 'Baja'], 
                                          state='readonly', width=20)
            prioridad_combo.grid(row=row_offset, column=1, sticky=tk.W, pady=5)
            row_offset += 1
        
        if item['tipo'] == 'evento':
            ttk.Label(main_frame, text="Lugar:").grid(row=row_offset, column=0, sticky=tk.W, pady=5)
            lugar_entry = ttk.Entry(main_frame, width=50)
            lugar_entry.insert(0, item.get('lugar', ''))
            lugar_entry.grid(row=row_offset, column=1, sticky=(tk.W, tk.E), pady=5)
            row_offset += 1
        
        ttk.Label(main_frame, text="Notas:").grid(row=row_offset, column=0, sticky=tk.W, pady=5)
        notas_entry = ttk.Entry(main_frame, width=50)
        notas_entry.insert(0, item.get('notas', ''))
        notas_entry.grid(row=row_offset, column=1, sticky=(tk.W, tk.E), pady=5)
        row_offset += 1
        
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=row_offset, column=0, columnspan=2, pady=20)
        
        def guardar():
            titulo = titulo_entry.get().strip()
            if not titulo:
                messagebox.showerror("Error", "El título no puede estar vacío")
                return
            
            fecha_inicio = fecha_entry.get().strip()
            try:
                datetime.strptime(fecha_inicio, '%Y-%m-%d')
            except:
                messagebox.showerror("Error", "Formato de fecha inválido. Use YYYY-MM-DD")
                return
            
            repetir = repetir_var.get() if item['tipo'] in ['tarea', 'evento'] else item.get('repetir', False)
            frecuencia = frecuencia_var.get() if repetir else None
            fecha_fin = fecha_fin_entry.get().strip() if repetir and item['tipo'] in ['tarea', 'evento'] else None
            
            if fecha_fin:
                try:
                    datetime.strptime(fecha_fin, '%Y-%m-%d')
                except:
                    messagebox.showerror("Error", "Formato de fecha fin inválido")
                    return
            
            prioridad = prioridad_var.get() if item['tipo'] == 'tarea' else 'Media'
            lugar = lugar_entry.get().strip() if item['tipo'] == 'evento' else ''
            notas = notas_entry.get().strip()
            
            edad = None
            if item['tipo'] == 'cumpleanos':
                fecha_nac = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
                hoy = date.today()
                edad = hoy.year - fecha_nac.year
                if hoy.month < fecha_nac.month or (hoy.month == fecha_nac.month and hoy.day < fecha_nac.day):
                    edad -= 1
            
            success, result = self.agenda.editar_item(
                item_id, titulo, desc_entry.get().strip(), fecha_inicio,
                repetir, frecuencia, fecha_fin, prioridad, lugar, notas, edad
            )
            
            if success:
                messagebox.showinfo("Éxito", f"✅ {result}")
                dialog.destroy()
                self.actualizar_lista()
                self.on_select(None)
            else:
                messagebox.showerror("Error", f"❌ {result}")
        
        ttk.Button(button_frame, text="💾 Guardar cambios", command=guardar).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="❌ Cancelar", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def dialogo_item(self, tipo):
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Nuevo {tipo.capitalize()}")
        dialog.geometry("650x750")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)
        
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")
        
        canvas = tk.Canvas(dialog)
        scrollbar = ttk.Scrollbar(dialog, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        main_frame = ttk.Frame(scrollable_frame, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_frame, text=f"📝 Nuevo {tipo.capitalize()}", 
                 font=('Arial', 14, 'bold')).grid(row=0, column=0, columnspan=2, pady=10)
        
        ttk.Label(main_frame, text="Título/Nombre:*").grid(row=1, column=0, sticky=tk.W, pady=5)
        titulo_entry = ttk.Entry(main_frame, width=50)
        titulo_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(main_frame, text="Descripción:").grid(row=2, column=0, sticky=tk.W, pady=5)
        desc_entry = ttk.Entry(main_frame, width=50)
        desc_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(main_frame, text="Fecha inicio (YYYY-MM-DD):*").grid(row=3, column=0, sticky=tk.W, pady=5)
        fecha_entry = ttk.Entry(main_frame, width=50)
        fecha_entry.insert(0, date.today().strftime('%Y-%m-%d'))
        fecha_entry.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=5)
        
        repetir_var = tk.BooleanVar(value=False)
        frecuencia_var = tk.StringVar(value='mensual')
        
        if tipo in ['tarea', 'evento']:
            ttk.Label(main_frame, text="¿Repetir?").grid(row=4, column=0, sticky=tk.W, pady=5)
            chk_repetir = ttk.Checkbutton(main_frame, variable=repetir_var)
            chk_repetir.grid(row=4, column=1, sticky=tk.W, pady=5)
            
            repetir_frame = ttk.LabelFrame(main_frame, text="Opciones de repetición", padding="10")
            repetir_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
            
            ttk.Label(repetir_frame, text="Frecuencia:").grid(row=0, column=0, sticky=tk.W, pady=5)
            frecuencias = ['diaria', 'semanal', 'quincenal', 'mensual', 'bimestral', 
                          'trimestral', 'cuatrimestral', 'semestral', 'anual']
            frecuencia_combo = ttk.Combobox(repetir_frame, textvariable=frecuencia_var, 
                                           values=frecuencias, state='readonly', width=30)
            frecuencia_combo.grid(row=0, column=1, sticky=tk.W, pady=5)
            
            ttk.Label(repetir_frame, text="Fecha fin (opcional):").grid(row=1, column=0, sticky=tk.W, pady=5)
            fecha_fin_entry = ttk.Entry(repetir_frame, width=30)
            fecha_fin_entry.grid(row=1, column=1, sticky=tk.W, pady=5)
            
            def toggle_repetir():
                if repetir_var.get():
                    frecuencia_combo.config(state='readonly')
                    fecha_fin_entry.config(state='normal')
                else:
                    frecuencia_combo.config(state='disabled')
                    fecha_fin_entry.config(state='disabled')
            
            repetir_var.trace('w', lambda *args: toggle_repetir())
            toggle_repetir()
        
        row_offset = 6 if tipo in ['tarea', 'evento'] else 5
        
        if tipo == 'tarea':
            ttk.Label(main_frame, text="Prioridad:").grid(row=row_offset, column=0, sticky=tk.W, pady=5)
            prioridad_var = tk.StringVar(value='Media')
            prioridad_combo = ttk.Combobox(main_frame, textvariable=prioridad_var, 
                                          values=['Alta', 'Media', 'Baja'], 
                                          state='readonly', width=20)
            prioridad_combo.grid(row=row_offset, column=1, sticky=tk.W, pady=5)
            row_offset += 1
        
        if tipo == 'evento':
            ttk.Label(main_frame, text="Lugar:").grid(row=row_offset, column=0, sticky=tk.W, pady=5)
            lugar_entry = ttk.Entry(main_frame, width=50)
            lugar_entry.grid(row=row_offset, column=1, sticky=(tk.W, tk.E), pady=5)
            row_offset += 1
        
        ttk.Label(main_frame, text="Notas:").grid(row=row_offset, column=0, sticky=tk.W, pady=5)
        notas_entry = ttk.Entry(main_frame, width=50)
        notas_entry.grid(row=row_offset, column=1, sticky=(tk.W, tk.E), pady=5)
        row_offset += 1
        
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=row_offset, column=0, columnspan=2, pady=20)
        
        def guardar():
            titulo = titulo_entry.get().strip()
            if not titulo:
                messagebox.showerror("Error", "El título no puede estar vacío")
                return
            
            fecha_inicio = fecha_entry.get().strip()
            try:
                datetime.strptime(fecha_inicio, '%Y-%m-%d')
            except:
                messagebox.showerror("Error", "Formato de fecha inválido. Use YYYY-MM-DD")
                return
            
            repetir = repetir_var.get() if tipo in ['tarea', 'evento'] else False
            frecuencia = frecuencia_var.get() if repetir else None
            fecha_fin = fecha_fin_entry.get().strip() if repetir and tipo in ['tarea', 'evento'] else None
            
            if fecha_fin:
                try:
                    datetime.strptime(fecha_fin, '%Y-%m-%d')
                except:
                    messagebox.showerror("Error", "Formato de fecha fin inválido")
                    return
            
            prioridad = prioridad_var.get() if tipo == 'tarea' else 'Media'
            lugar = lugar_entry.get().strip() if tipo == 'evento' else ''
            notas = notas_entry.get().strip()
            
            edad = None
            if tipo == 'cumpleanos':
                fecha_nac = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
                hoy = date.today()
                edad = hoy.year - fecha_nac.year
                if hoy.month < fecha_nac.month or (hoy.month == fecha_nac.month and hoy.day < fecha_nac.day):
                    edad -= 1
            
            success, result = self.agenda.agregar_item(
                tipo, titulo, desc_entry.get().strip(), fecha_inicio,
                repetir, frecuencia, fecha_fin, prioridad, lugar, notas, edad
            )
            
            if success:
                messagebox.showinfo("Éxito", f"✅ Item creado con ID: {result}")
                dialog.destroy()
                self.actualizar_lista()
            else:
                messagebox.showerror("Error", f"❌ Error al crear: {result}")
        
        ttk.Button(button_frame, text="💾 Guardar", command=guardar).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="❌ Cancelar", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def completar_tarea(self):
        if self.item_id_actual is None:
            messagebox.showwarning("Advertencia", "Selecciona una tarea primero")
            return
        
        item = self.agenda.items.get(self.item_id_actual)
        
        if not item:
            messagebox.showerror("Error", "Item no encontrado")
            self.item_id_actual = None
            return
        
        if item['tipo'] != 'tarea':
            messagebox.showwarning("Advertencia", "El item seleccionado no es una tarea")
            return
        
        if not item.get('repetir', False):
            success, msg = self.agenda.completar_tarea_normal(self.item_id_actual)
            if success:
                messagebox.showinfo("Éxito", msg)
                self.actualizar_lista()
                self.on_select(None)
            else:
                messagebox.showerror("Error", msg)
        else:
            self.dialogo_completar_ocurrencia(self.item_id_actual)
    
    def dialogo_completar_ocurrencia(self, item_id):
        item = self.agenda.items.get(item_id)
        if not item:
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Completar ocurrencia - {item['titulo']}")
        dialog.geometry("500x450")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)
        
        main_frame = ttk.Frame(dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_frame, text=f"📋 Tarea: {item['titulo']}", font=('Arial', 12, 'bold')).pack(pady=10)
        
        ocurrencias = item.get('ocurrencias', {})
        pendientes = [(fecha, occ) for fecha, occ in ocurrencias.items() 
                     if not occ.get('completada', False)]
        
        if not pendientes:
            messagebox.showinfo("Info", "🎉 No hay ocurrencias pendientes")
            dialog.destroy()
            return
        
        ttk.Label(main_frame, text=f"Ocurrencias pendientes: {len(pendientes)}").pack(pady=5)
        ttk.Label(main_frame, text="Selecciona la ocurrencia a completar:").pack(pady=5)
        
        listbox_frame = ttk.Frame(main_frame)
        listbox_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        scrollbar = ttk.Scrollbar(listbox_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        listbox = tk.Listbox(listbox_frame, yscrollcommand=scrollbar.set, height=8, font=('Arial', 10))
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=listbox.yview)
        
        for fecha, _ in sorted(pendientes):
            listbox.insert(tk.END, f"📅 {fecha}")
        
        def completar_seleccionada():
            selection = listbox.curselection()
            if not selection:
                messagebox.showwarning("Advertencia", "Selecciona una ocurrencia")
                return
            
            fecha = listbox.get(selection[0]).replace("📅 ", "")
            success, msg = self.agenda.completar_ocurrencia(item_id, fecha)
            
            if success:
                messagebox.showinfo("Éxito", f"✅ {msg}")
                dialog.destroy()
                self.actualizar_lista()
                self.on_select(None)
            else:
                messagebox.showerror("Error", f"❌ {msg}")
        
        def completar_todas():
            if messagebox.askyesno("Confirmar", "¿Completar todas las ocurrencias pendientes?"):
                success, msg = self.agenda.completar_todas_ocurrencias(item_id)
                if success:
                    messagebox.showinfo("Éxito", f"✅ {msg}")
                    dialog.destroy()
                    self.actualizar_lista()
                    self.on_select(None)
                else:
                    messagebox.showerror("Error", f"❌ {msg}")
        
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="✅ Completar seleccionada", 
                  command=completar_seleccionada).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="✅ Completar todas", 
                  command=completar_todas).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="❌ Cancelar", 
                  command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def ver_estadisticas(self):
        if self.item_id_actual is None:
            messagebox.showwarning("Advertencia", "Selecciona una tarea primero")
            return
        
        item = self.agenda.items.get(self.item_id_actual)
        
        if not item:
            messagebox.showerror("Error", "Item no encontrado")
            self.item_id_actual = None
            return
        
        if item['tipo'] != 'tarea':
            messagebox.showwarning("Advertencia", "El item seleccionado no es una tarea")
            return
        
        if not item.get('repetir', False):
            messagebox.showinfo("Info", "Esta tarea no es repetitiva, no tiene estadísticas")
            return
        
        stats = self.agenda.obtener_estadisticas(self.item_id_actual)
        
        if not stats:
            messagebox.showinfo("Info", "No hay estadísticas disponibles")
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Estadísticas - {item['titulo']}")
        dialog.geometry("650x500")
        dialog.transient(self.root)
        dialog.grab_set()
        
        main_frame = ttk.Frame(dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_frame, text=f"📊 Estadísticas de: {item['titulo']}", 
                 font=('Arial', 14, 'bold')).pack(pady=10)
        
        summary_frame = ttk.Frame(main_frame)
        summary_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(summary_frame, text=f"Total: {stats['total']}", 
                 font=('Arial', 11)).pack(side=tk.LEFT, padx=20)
        ttk.Label(summary_frame, text=f"✅ Completadas: {stats['completadas']} ({stats['porcentaje']:.1f}%)", 
                 font=('Arial', 11)).pack(side=tk.LEFT, padx=20)
        ttk.Label(summary_frame, text=f"⏳ Pendientes: {stats['pendientes']}", 
                 font=('Arial', 11)).pack(side=tk.LEFT, padx=20)
        
        progress_frame = ttk.Frame(main_frame)
        progress_frame.pack(fill=tk.X, pady=10)
        
        progress = ttk.Progressbar(progress_frame, length=400, mode='determinate', 
                                  value=stats['porcentaje'])
        progress.pack(pady=5)
        
        text_frame = ttk.Frame(main_frame)
        text_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        text = scrolledtext.ScrolledText(text_frame, wrap=tk.WORD, height=12, font=('Arial', 10))
        text.pack(fill=tk.BOTH, expand=True)
        
        info = ""
        if stats['completadas'] > 0:
            info += "✅ OCURRENCIAS COMPLETADAS:\n"
            for fecha, occ in sorted(stats['completadas_list']):
                info += f"  📅 {fecha} - Completada el: {occ.get('completada_en', 'N/A')}\n"
        
        if stats['pendientes'] > 0:
            if info:
                info += "\n"
            info += "⏳ OCURRENCIAS PENDIENTES:\n"
            for fecha, _ in sorted(stats['pendientes_list']):
                info += f"  📅 {fecha}\n"
        
        text.insert(1.0, info)
        text.config(state='disabled')
        
        ttk.Button(main_frame, text="Cerrar", command=dialog.destroy).pack(pady=10)
    
    def eliminar_item(self):
        if self.item_id_actual is None:
            messagebox.showwarning("Advertencia", "Selecciona un item primero")
            return
        
        item = self.agenda.items.get(self.item_id_actual)
        if not item:
            messagebox.showerror("Error", "Item no encontrado")
            self.item_id_actual = None
            return
        
        if messagebox.askyesno("Confirmar", f"¿Eliminar '{item['titulo']}'?"):
            success, msg = self.agenda.eliminar_item(self.item_id_actual)
            if success:
                messagebox.showinfo("Éxito", msg)
                self.item_id_actual = None
                self.actualizar_lista()
                self.detail_text.delete(1.0, tk.END)
            else:
                messagebox.showerror("Error", msg)
    
    def ver_hoy(self):
        recordatorios = self.agenda.obtener_recordatorios_hoy()
        
        if not recordatorios:
            messagebox.showinfo("Recordatorios", "📭 No hay nada programado para hoy")
            return
        
        mensaje = "📆 RECORDATORIOS PARA HOY\n" + "="*40 + "\n\n"
        for id_item, item in recordatorios:
            emojis = {'tarea': '⏰', 'evento': '📅', 'cumpleanos': '🎂', 'feriado': '🎉'}
            mensaje += f"{emojis.get(item['tipo'], '📌')} {item['titulo']}\n"
            if item['tipo'] == 'evento' and item.get('lugar'):
                mensaje += f"  📍 Lugar: {item['lugar']}\n"
            if item['tipo'] == 'cumpleanos':
                mensaje += f"  🎂 Edad: {item.get('edad', '?')} años\n"
            mensaje += "\n"
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Recordatorios de hoy")
        dialog.geometry("500x400")
        dialog.transient(self.root)
        
        text = scrolledtext.ScrolledText(dialog, wrap=tk.WORD, font=('Arial', 10))
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text.insert(1.0, mensaje)
        text.config(state='disabled')
        
        ttk.Button(dialog, text="Cerrar", command=dialog.destroy).pack(pady=10)
    
    def ver_proximos_dias(self):
        proximos = self.agenda.obtener_proximos_dias(7)
        
        mensaje = "📅 PRÓXIMOS 7 DÍAS\n" + "="*40 + "\n\n"
        
        hay_items = False
        for fecha_str in sorted(proximos.keys()):
            if proximos[fecha_str]:
                fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
                mensaje += f"📌 {fecha.strftime('%A %d/%m/%Y').upper()}:\n"
                for id_item, item in proximos[fecha_str]:
                    emojis = {'tarea': '⏰', 'evento': '📅', 'cumpleanos': '🎂', 'feriado': '🎉'}
                    mensaje += f"  {emojis.get(item['tipo'], '📌')} {item['titulo']}\n"
                mensaje += "\n"
                hay_items = True
        
        if not hay_items:
            mensaje += "📭 No hay nada programado para los próximos 7 días"
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Próximos 7 días")
        dialog.geometry("500x400")
        dialog.transient(self.root)
        
        text = scrolledtext.ScrolledText(dialog, wrap=tk.WORD, font=('Arial', 10))
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text.insert(1.0, mensaje)
        text.config(state='disabled')
        
        ttk.Button(dialog, text="Cerrar", command=dialog.destroy).pack(pady=10)
    
    def exportar_csv(self):
        from tkinter import filedialog
        
        archivo = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if archivo:
            self.agenda.exportar_csv('tarea', archivo)
            messagebox.showinfo("Éxito", f"✅ Datos exportados a {archivo}")
    
    def exportar_json(self):
        from tkinter import filedialog
        
        archivo = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if archivo:
            self.agenda.exportar_json_completo(archivo)
            messagebox.showinfo("Éxito", f"✅ Datos exportados a {archivo}")
    
    def acerca_de(self):
        messagebox.showinfo("Acerca de", 
                           "📚 Agenda Completa v4.0\n\n"
                           "Una aplicación de agenda con soporte para:\n"
                           "• Tareas normales y repetitivas\n"
                           "• Eventos\n"
                           "• Cumpleaños\n"
                           "• Feriados\n\n"
                           "Características:\n"
                           "• Frecuencias personalizables\n"
                           "• Historial de completados\n"
                           "• Estadísticas de progreso\n"
                           "• Edición de items\n"
                           "• Exportación a CSV y JSON\n\n"
                           "Desarrollado con Python y Tkinter")


def main():
    root = tk.Tk()
    app = AgendaApp(root)
    root.mainloop()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 ¡Hasta pronto!")
        sys.exit(0)