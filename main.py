import kivy
import gspread
from PIL import Image
from datetime import date
from time import ctime, gmtime
from pyzbar.pyzbar import decode
from oauth2client.service_account import ServiceAccountCredentials

kivy.require('2.0.0')
from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.uix.screenmanager import Screen, ScreenManager


scope = [
	"https://spreadsheets.google.com/feeds",
	"https://www.googleapis.com/auth/spreadsheets",
	"https://www.googleapis.com/auth/drive.file",
	"https://www.googleapis.com/auth/drive"
]

creds = ServiceAccountCredentials.from_json_keyfile_name("sigit-apps-cc25c0f862ec.json", scope)
client = gspread.authorize(creds)
s = client.open('Datos-Molino')

Builder.load_string('''
<CameraScreen>:
	BoxLayout:
		orientation: 'vertical'    
		Camera:
			id: camera
			resolution: (640, 480)
			play: False       
<Molino>:
	GridLayout:
		cols:1
		rows:8
		padding: 10
		apacing: 5
		canvas:
			Color: 
				rgb: 1, 1, 1
			Rectangle:
				size: self.size
				pos: self.pos

		Image: 
			source: 'SIGIT.jpg'
			size_hint_x: 0.21
			allow_stretch: True

		ToggleButton:
			text: 'Abrir Escaner'
			on_press: root.open_camera()
			height: '48dp'
			size_hint: .5, .95
			pos_hint: {"center_x": .5, "center_y": .5}
			bold: True
			font_size: 50

		Label: 
			text: 'Nombre y apellidos: '
			color: 0,0,0
			size_hint: .5, .95
			font_size: 50
			markup: True
			size: self.texture_size
			bold: True

		TextInput:
			id: name
			pos_hint: {'center_x': 0.5, 'center_y': 0.705}
			size_hint: .5, .95
			focus: True
			multiline: False

		Label: 
			text: 'Cantidad Molido (en Kg): '
			color: 0,0,0
			size_hint: .5, .95
			font_size: 50
			markup: True
			bold: True

		TextInput:
			id: cantidad
			pos_hint: {'center_x': 0.5, 'center_y': 0.705}
			size_hint: .5, .95 
			focus: True
			multiline: False

		Button:
			id: guardar
			text: 'Guardar'
			on_press: root.Guardar()
			height: '48dp'
			size_hint: .5, .95
			pos_hint: {"center_x": .5, "center_y": .5}
			bold: True
			font_size: 50

<ScreenManager>:
	Molino:
	CameraScreen:
''')

class Molino(Screen):
	qr_model = ''

	def open_camera(self):
		self.manager.current = 'camera'

	def set_qr_model(self, qr_code_data):
		self.qr_model = qr_code_data
		Aviso_pop(self.qr_model)

	def Guardar(self):
		if self.qr_model == '':
			error("Escanea el qr del material")
		elif self.ids.cantidad.text == '':
			error("Introducir Cantidad de material molido")
		elif self.ids.name.text == '':
			error("Introducir nombre")
		else:
			Guardar_datos(int(self.ids.cantidad.text),self.qr_model,self.ids.name.text)

def buscar_vacia(sheet):
	j = 1
	for i in sheet.col_values(1):
		j = j + 1
		if sheet.cell(j,1).value is None:
			return j

def Guardar_datos(Cantidad, qr_model, name):
	layout = GridLayout(cols=1, padding=10)
	popup = Popup(title="Guardar",
				content=layout,
				size_hint=(.5, .5))

	popupLabel = Label(text="Has molido: {}Kg de {} \n ¿estás seguro?".format(Cantidad,qr_model))
	yesbutton = Button(text="Si", size_hint=(.3, .3))
	closeButton = Button(text="No", size_hint=(.3, .3))

	layout.add_widget(popupLabel)
	layout.add_widget(yesbutton)
	layout.add_widget(closeButton)

	popup.open()

	closeButton.bind(on_press=popup.dismiss)

	yesbutton.bind(on_press= lambda x:datos(Cantidad, qr_model, name))
	yesbutton.bind(on_press=popup.dismiss)

def datos(Cantidad, qr_model, name):
	sheet1 = s.worksheet("Hoja 1")

	year = gmtime()[0]
	month = gmtime()[1]
	day = gmtime()[2]
	week = date(year,month,day).isocalendar().week
	if week < 10: 
		week = "0{}".format(week)
	Lote = "{}{}".format(year,week)

	try:
			Time = ''
			Time = ctime()
			a = buscar_vacia(sheet1)
			sheet1.update_cell(a, 1, Time)
			sheet1.update_cell(a, 2, name)
			sheet1.update_cell(a, 3, int(Cantidad))
			sheet1.update_cell(a, 4, qr_model)
			sheet1.update_cell(a, 5, Lote)

			Aviso_pop("Hecho")
			qr_model = ' '

	except (ValueError, NameError, TypeError):
		error("Error! Avisar al encargado")

def Aviso_pop(text):
	layout = GridLayout(cols=1, padding=10)
	popup = Popup(title="Aviso!",
					content=layout,
					size_hint=(.5, .5))

	popupLabel = Label(text=text)
	closeButton = Button(text="cerrar", size_hint=(.3, .3))

	layout.add_widget(popupLabel)
	layout.add_widget(closeButton)

	popup.open()

	closeButton.bind(on_press=popup.dismiss)

def error(text):
	layout = GridLayout(cols=1, padding=10)
	popup = Popup(title="Error",
					content=layout,
					size_hint=(.5, .5))

	popupLabel = Label(text=text)
	closeButton = Button(text="Cerrar", size_hint=(.3, .3))

	layout.add_widget(popupLabel)
	layout.add_widget(closeButton)

	popup.open()

	closeButton.bind(on_press=popup.dismiss)

class CameraScreen(Screen):
	camera_active = False
	qr_detected = False

	def on_enter(self):
		self.camera = self.ids.camera
		self.qr_detected = False
		self.camera.play = True
		Clock.schedule_interval(self.decode_qr, 1 / 30)
		self.camera_active = True

	def on_leave(self):
		if self.camera is not None:
			self.camera.play = False
			Clock.unschedule(self.decode_qr)
			self.camera_active = False

	def close_camera(self):
		self.manager.current = 'molino'

	def decode_qr(self, dt):
		image_data = self.camera.texture.pixels
		width, height = self.camera.resolution
		image = Image.frombytes(mode='RGBA', size=(width, height), data=image_data)
		decoded_qr_codes = decode(image)

		if not self.qr_detected and len(decoded_qr_codes) > 0:
			qr_code_data = decoded_qr_codes[0].data.decode('utf-8')
			mainscreen = self.manager.get_screen('molino')
			mainscreen.set_qr_model(qr_code_data)
			self.qr_detected = True
			self.manager.current = 'molino'

class mainApp(App):
	title = "Sigit-Molino"
	def build(self):
		sm = ScreenManager()
		sm.add_widget(Molino(name='molino'))
		sm.add_widget(CameraScreen(name='camera'))
		return sm


if __name__ == '__main__':
	mainApp().run()