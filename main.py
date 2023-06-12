import telebot
from telebot import types
import datetime
import qrcode
import sqlite3 as sql
import os

# bot = telebot.TeleBot('6108708700:AAHVPv0tlRG4YZ04Un5aLCuZP6Z3dkKfmaM')

#test token
bot = telebot.TeleBot('5965612779:AAGLUd1dAYECil8qOqEWKeV1Ut7wqakdR9Y')


#https://t.me/MiamiRegBot?start=p


#глобальные переменные 
promo_id = 1
guest_name = ""
phone = ""
date = None

mail_text=""
Image , Video = False , False

@bot.message_handler(commands = ['start'])
def main(message):
	global promo_id

	#ловим id промоутера из ссылки и проверив на корректность добавляем
	if len(message.text.split(' ')) >=2:
		raw_promo_id = message.text.split(' ')[1]
	else:
		raw_promo_id = "1"
		print("-->> переход по битой реферальной ссылке")

	if (raw_promo_id.isdigit()):
		promo_id = int(raw_promo_id)
		bot.send_message(message.chat.id, "Добро пожаловать в бот Miami Club!\nДавайте пройдем небольшую регистрацию - напишите свое имя.")
		bot.register_next_step_handler(message,get_name)		
	else:
		#если перейти по qr коду выданному госю, то сотрудник увидит информацию о нем
		if raw_promo_id[0] == "x":
			guest_id = raw_promo_id[1:]
			who_just_came(message,guest_id)
			print("-->> принят билет")
		elif raw_promo_id[0] == "a":
			register_admin(message)
		elif raw_promo_id[0] == "p":
			bot.send_message(message.chat.id, "Вы были приглашены на роль промоутера, введите свое имя и вам будет выдана персональная ссылка для приглашения гостей.")
			bot.register_next_step_handler(message,register_promo)
		elif raw_promo_id[0] == "t":
			return
		else:
			#при битой ссылке гостя получит мнимый промоутер
			bot.send_message(message.chat.id, "Добро пожаловать в бот Miami Club!\nДавайте пройдем небольшую регистрацию - напишите свое имя.")
			bot.register_next_step_handler(message,get_name)


@bot.message_handler(commands = ['stat'])
def main(message):
	print("--->> вызвана команда /stat")
	with sql.connect("bot.sql") as con:
		cur = con.cursor()
		cur.execute("SELECT * FROM main_promo WHERE chat_id = "+str(message.chat.id))
		result = cur.fetchall()

	if len(result) == 0:
		bot.send_message(message.chat.id, "Вы должны быть Генеральным промоутером чтобы использовать эту команду")
		print("-->> команда stat не выполнена из-за отсутсвия прав")
	else:
		with sql.connect("bot.sql") as con:
			cur = con.cursor()
			cur.execute("SELECT promo.name , promo.id  FROM promo JOIN promo_users ON promo.id = promo_users.promo_id WHERE promo_users.date BETWEEN datetime('now', '-6 days') AND datetime('now', 'localtime')")
			promos = cur.fetchall()

		invite_list = {}
		for el in promos:
			if not el[0] in invite_list.keys():
				invite_list[el[0]] = 1
			else:
				invite_list[el[0]] += 1

		text = "За последнюю неделю промоутеры привели "+str(len(promos))+" зарегестрировавшихся гостей, из них:"
		for key, value in invite_list.items():
			text += "\n"+key +": "+str(value)
		bot.send_message(message.chat.id, text)
		print("-->> команда stat выполнена")
		

@bot.message_handler(commands = ['send'])
def main(message):
	print("--->> вызвана команда /send")
	with sql.connect("bot.sql") as con:
		cur = con.cursor()
		cur.execute("SELECT * FROM main_promo WHERE chat_id = "+str(message.chat.id))
		result = cur.fetchall()

	if len(result) == 0:
		bot.send_message(message.chat.id, "Вы должны быть Генеральным промоутером чтобы использовать эту команду")
		print("-->> команда send не выполнена из-за отсутсвия прав")
	else:
		bot.send_message(message.chat.id, "Отправте текстовое сообщение которое хотите разослать всем гостям")
		bot.register_next_step_handler(message, get_mailing)


def get_mailing(message):
	global mail_text
	mail_text = message.text

	markup = types.InlineKeyboardMarkup()
	markup.add(types.InlineKeyboardButton("Да" , callback_data = 'add_file'))
	markup.add(types.InlineKeyboardButton("Нет" , callback_data = 'mail_all'))

	bot.send_message(message.chat.id, "Хотите добавить к рассылке медиа файл?" , reply_markup = markup)
	


@bot.callback_query_handler(func = lambda callback: True)
def callback_message(callback):
	if callback.data == 'add_file':
		bot.send_message(callback.from_user.id, "загрузите файл")

	elif callback.data == 'mail_all':
		mail_all()



@bot.message_handler(content_types=['photo'])
def get_image(message):
	global Image
	print("--->> отправлено изображение")
	with sql.connect("bot.sql") as con:
		cur = con.cursor()
		cur.execute("SELECT * FROM main_promo WHERE chat_id = "+str(message.chat.id))
		result = cur.fetchall()

	if len(result) == 0:
		bot.send_message(message.chat.id, "Вы должны быть Генеральным промоутером чтобы загружать файлы")
		print("-->> фото не загружено из-за отсутсвия прав")
	else:
		try:
			chat_id = message.chat.id

			
			file_info = bot.get_file(message.photo[2].file_id)
			downloaded_file = bot.download_file(file_info.file_path)

			src = "image.png";
			with open(src, 'wb') as new_file:
				new_file.write(downloaded_file)


			markup = types.InlineKeyboardMarkup()
			markup.add(types.InlineKeyboardButton("Да" , callback_data = 'add_file'))
			markup.add(types.InlineKeyboardButton("Нет" , callback_data = 'mail_all'))

			Image = True
			bot.reply_to(message, "Фотография сохранена, хотите добавить еще видео?" , reply_markup = markup)
			
		except:
		 	print("-->> ошибка при загрузке фото")


@bot.message_handler(content_types=['video'])
def get_video(message):
	global Video
	print("--->> отправлено видео")
	with sql.connect("bot.sql") as con:
		cur = con.cursor()
		cur.execute("SELECT * FROM main_promo WHERE chat_id = "+str(message.chat.id))
		result = cur.fetchall()

	if len(result) == 0:
		bot.send_message(message.chat.id, "Вы должны быть Генеральным промоутером чтобы загружать файлы")
		print("-->> видео не загружено из-за отсутсвия прав")
	else:
		try:
			chat_id = message.chat.id

			
			file_info = bot.get_file(message.video.file_id)
			downloaded_file = bot.download_file(file_info.file_path)

			src = "video.mp4";
			with open(src, 'wb') as new_file:
				new_file.write(downloaded_file)


			markup = types.InlineKeyboardMarkup()
			markup.add(types.InlineKeyboardButton("Да" , callback_data = 'add_file'))
			markup.add(types.InlineKeyboardButton("Нет" , callback_data = 'mail_all'))

			Video = True
			bot.reply_to(message, "Видео сохранено, хотите добавить еще фото?" , reply_markup = markup)

		except:
		 	print("-->> ошибка при загрузке видео")


def mail_all():
	global mail_text , Video , Image
	with sql.connect("bot.sql") as con:
		cur = con.cursor()
		cur.execute("SELECT chat_id FROM users")
		chat_id = cur.fetchall()

	for i in range(len(chat_id)):
		if Image:
			with open('image.png', 'rb') as file:
				bot.send_photo(chat_id[i][0], photo=file)
		if Video:
			with open('video.mp4', 'rb') as file:
				bot.send_video(chat_id[i][0], video=file)	

		bot.send_message(chat_id[i][0], mail_text)	

		Video , Image = False , False


def get_name(message):
	global guest_name
	guest_name = message.text
	try:
		if not set(".,:;!_*-+()/#¤%&").isdisjoint(guest_name):
			bot.send_message(message.chat.id, "Имя не должно содержать спец символов, попробуйте еще раз")
			bot.register_next_step_handler(message, get_name)
		else:
			markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
			markup.add(telebot.types.KeyboardButton(text='Отправить номер телефона', request_contact=True))
			bot.send_message(message.chat.id, "Теперь отправьте мне свой номер телефона с помощью кнопки ниже.", reply_markup=markup)

			bot.register_next_step_handler(message, get_phone)
	except:
		bot.send_message(message.chat.id, "Неверно введено имя, попробуйте еще раз")
		bot.register_next_step_handler(message, get_name)


def get_phone(message):
	global phone

	try:
		phone = message.contact.phone_number
		if phone == "":
			bot.send_message(message.chat.id, "номер телефона должен быть введен через кнопку")
			bot.register_next_step_handler(message, get_phone)
		else:
			with sql.connect("bot.sql") as con:
				cur = con.cursor()
				cur.execute("SELECT * FROM users WHERE phone = "+phone)
				result = cur.fetchall()

			if len(result) != 0:
				bot.send_message(message.chat.id, "данный номер телефона уже зарегестрирован")
			else:
				bot.send_message(message.chat.id, "введите свою дату рождения в формате дд.мм.гггг")
				bot.register_next_step_handler(message, get_date)
	except:
		bot.send_message(message.chat.id, "Вы ввели телефон неправильно, попробуйте еще раз ")
		bot.register_next_step_handler(message, get_phone)

def get_date(message):
	global guest_name , phone , date , promo_id
	try:
		raw_date = message.text.split('.')
	except:
		wrong_date(message)
		return

	if (len(raw_date) == 3 and raw_date[0].isdigit() and raw_date[1].isdigit() and raw_date[2].isdigit()):
		if(int(raw_date[2])>=1900 and int(raw_date[1])<=12 and int(raw_date[0])<=31):
			print("-->> введены данные о дате рождения")

			try:
				date = datetime.datetime(int(raw_date[2]) , int(raw_date[1]) , int(raw_date[0]))

				now = datetime.datetime.now()
				delta = now - date
				#если прожил больше дней чем надо на 18 лет - регестрируем
				if delta.days <= 6570:
					bot.send_message(message.chat.id,"Извините, для продолжения вам должно быть 18 лет или старше.")
				else:
					bot.send_message(message.chat.id, "Вы вошли в систему! Теперь вы можете получить билет.")

					date_of_birth_str = str(date.day) +"."+ str(date.month) +"."+ str(date.year)

					print("-->> нового гостя заносит в БД")
					with sql.connect("bot.sql") as con:
						cur = con.cursor()
						val = "'"+str(message.chat.id)+"','"+guest_name+"','"+phone+"','"+date_of_birth_str+"','"+str(promo_id)+"'"
						cur.execute("INSERT INTO users (chat_id, name, phone, bdate, promo_id) VALUES ("+val+")")
						cur.execute("SELECT last_insert_rowid()")
						cur_id = cur.fetchall()
						cur.execute("INSERT INTO promo_users (promo_id , user_id ) VALUES ('"+str(promo_id)+"','"+str(cur_id[0][0])+"')")

					#отправляем уведомление о регистрации сотрудникам
					call_promo("По вашей ссылке зарегистрирован гость " , cur_id[0][0])
					call_admins("Зарегистрирован гость " , cur_id[0][0])

					print("-->> отправляется кр код")
					#после добавления БД оставить в QR коде только ссылку на бота с доб инфой его id в таблице
					qr_data = f"https://t.me/MiamiRegBot?start=x"+str(cur_id[0][0])
					qr = qrcode.make(qr_data)
					qr.save('qr_code.png')  # Сохраняем QR-код как изображение
					with open('qr_code.png', 'rb') as qr_file:
						bot.send_photo(message.chat.id, photo=qr_file)

			except:
				print("-->> сработал эксепт в get_date")
				wrong_date(message)

		else:
			wrong_date(message)

	else:
		wrong_date(message)

def wrong_date(message):
	bot.send_message(message.chat.id, "дата рождения введена неверно, попробуйте еще раз")
	bot.register_next_step_handler(message, get_date)

#тут посмотрим по БД кому конкретно придут уведомления
def call_promo(text , guest_id):
	global promo_id
	with sql.connect("bot.sql") as con:
		cur = con.cursor()
		cur.execute("SELECT * FROM promo_users WHERE user_id = "+str(guest_id))
		result = cur.fetchall()

	if len(result)!=1:
		print("-->> что-то пошло не так с отправкой уведомления промоутеру" )
	else:
		promo_id = result[0][1]
		if promo_id == 1:
			return

		with sql.connect("bot.sql") as con:
			cur = con.cursor()
			cur.execute("SELECT * FROM promo WHERE id = "+str(promo_id))
			result2 = cur.fetchall()
		if len(result2) !=1:
			print("-->> что-то пошло не так с отправкой уведомления промоутеру" )
		else:
			promo_chat = result2[0][1]
			with sql.connect("bot.sql") as con:
				cur = con.cursor()
				cur.execute("SELECT * FROM users WHERE id = "+str(guest_id))
				result3 = cur.fetchall()

			user_name = result3[0][2]

			bot.send_message(promo_chat,text+user_name)

def call_admins(text , guest_id):
	with sql.connect("bot.sql") as con:
		cur = con.cursor()
		cur.execute("SELECT * FROM promo_users WHERE user_id = "+str(guest_id))
		result = cur.fetchall()
	if len(result)!=1:
		print("-->> что-то пошло не так с отправкой уведомления админу" )
	else:
		promo_id = result[0][1]
		with sql.connect("bot.sql") as con:
			cur = con.cursor()
			cur.execute("SELECT * FROM promo WHERE id = "+str(promo_id))
			result2 = cur.fetchall()

		if len(result2) !=1:
			print("-->> что-то пошло не так с отправкой уведомления админу" )
		else:
			promo_name = result2[0][2]
			with sql.connect("bot.sql") as con:
				cur = con.cursor()
				cur.execute("SELECT * FROM main_promo")
				result3 = cur.fetchall()
			for admin in result3:
				bot.send_message(admin[1],text+"от промоутера "+promo_name)

#guest_id - строка
def who_just_came(message,guest_id):
	print("-->> начата проверка приглашения")
	global promo_id
	with sql.connect("bot.sql") as con:
		cur = con.cursor()
		cur.execute("SELECT * FROM users WHERE id = "+guest_id)
		result = cur.fetchall()
		if len(result) == 1:
			promo_id = result[0][5]

			with sql.connect("bot.sql") as con:
				cur = con.cursor()
				cur.execute("SELECT * FROM promo_users WHERE user_id = "+guest_id)
				result2 = cur.fetchall()

			if len(result2) == 1:
				with sql.connect("bot.sql") as con:
					cur = con.cursor()
					cur.execute("SELECT * FROM promo WHERE id = "+str(result2[0][1]))
					result3 = cur.fetchall()

					if len(result3)==1:
						promo_name = result3[0][2]				


			text = "Имя: "+result[0][2]+"\nПриглашён промоутером: "+promo_name
			bot.send_message(message.chat.id, text)

			#зовем админа и его промоутера
			call_promo("Пришел приглашенный вами гость ",result[0][0])
			call_admins("Пришел гость ",result[0][0])

		elif len(result) == 0:
			bot.send_message(message.chat.id, "Данные о госте отсутствуют")
	print("-->> закончена проверка приглашения")

def register_admin(message):
	print("-->> начата регистрация админа")
	with sql.connect("bot.sql") as con:
		cur = con.cursor()
		cur.execute("INSERT INTO main_promo (chat_id) VALUES ('"+str(message.chat.id)+"');")
	bot.send_message(message.chat.id, "Вы были зарегестрированы как Генеральный промоутер\nВам будут приходить уведомления обо всех событиях гостей и промоутеров, а так же вам доступна команда /stat")
	print("-->> завершена регистрация админа")

def register_promo(message):
	print("-->> начата регистрация промоутера")
	name = message.text
	with sql.connect("bot.sql") as con:
		cur = con.cursor()
		cur.execute("INSERT INTO promo (chat_id , name) VALUES ('"+str(message.chat.id)+"','" +name+"');")

		cur.execute("SELECT last_insert_rowid()")
		cur_id = cur.fetchall()
	cur_id = cur_id[0][0]

	bot.send_message(message.chat.id, "Вы были зарегистрированы как промоутер\nВаша персональная ссылка для приглашения: https://t.me/MiamiRegBot?start="+str(cur_id)+" и QR-код для этой ссылки:")

	qr_data = f"https://t.me/MiamiRegBot?start="+str(cur_id)
	qr = qrcode.make(qr_data)
	qr.save('qr_code_invite.png')  # Сохраняем QR-код как изображение
	with open('qr_code_invite.png', 'rb') as qr_file:
		bot.send_photo(message.chat.id, photo=qr_file)

	print("-->> завершена регистрация промоутера")





bot.polling(non_stop = True)