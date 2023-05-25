import telebot
import datetime
import qrcode
import sqlite3 as sql

bot = telebot.TeleBot('6108708700:AAHVPv0tlRG4YZ04Un5aLCuZP6Z3dkKfmaM')


#https://t.me/MiamiRegBot?start=2


#глобальные переменные 
promo_id = 1
guest_name = ""
phone = ""
date = None

@bot.message_handler(commands = ['start'])
def main(message):
	global promo_id

	#ловим id промоутера из ссылки и проверив на корректность добавляем
	raw_promo_id = message.text.split(' ')[1]
	if (raw_promo_id.isdigit()):
		promo_id = int(raw_promo_id)
		bot.send_message(message.chat.id, "Добро пожаловать в бот Майами Клуб!\nДавайте пройдем небольшую регистрацию - напишите свое имя.")
		bot.register_next_step_handler(message,get_name)		
	else:
		#если перейти по qr коду выданному госю, то сотрудник увидит информацию о нем
		if raw_promo_id[0] == "x":
			guest_id = raw_promo_id[1:]
			who_just_came(message,guest_id)
		elif raw_promo_id[0] == "a":
			register_admin(message)
		elif raw_promo_id[0] == "p":
			bot.send_message(message.chat.id, "Вы были приглашены на роль промоутера, введите свое имя и вам будет выдана персональная ссылка для приглашения гостей.")
			bot.register_next_step_handler(message,register_promo)
		else:
			#при битой ссылке гостя получит мнимый промоутер
			bot.send_message(message.chat.id, "Добро пожаловать в бот Майами Клуб!\nДавайте пройдем небольшую регистрацию - напишите свое имя.")
			bot.register_next_step_handler(message,get_name)


# #отлов дебиков которые неправильно ввели телефон
# @bot.message_handler()
# def info(message):
# 	bot.send_message(message.chat.id,"Вы ввели что-то не то, пожалуйста начните заново начиная с номера телефона ")
# 	bot.register_next_step_handler(message , get_phone)


def get_name(message):
	global guest_name
	guest_name = message.text

	if not set(".,:;!_*-+()/#¤%&)").isdisjoint(guest_name):
		bot.send_message(message.chat.id, "Имя не должно содержать спец символов, попробуйте еще раз")
		bot.register_next_step_handler(message, get_name)
	else:
		markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
		markup.add(telebot.types.KeyboardButton(text='Отправить номер телефона', request_contact=True))
		bot.send_message(message.chat.id, "Теперь отправьте мне свой номер телефона с помощью кнопки ниже.", reply_markup=markup)

		bot.register_next_step_handler(message, get_phone)

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
	raw_date = message.text.split('.')

	if (len(raw_date) == 3 and raw_date[0].isdigit() and raw_date[1].isdigit() and raw_date[2].isdigit()):
		if(int(raw_date[2])>=1900 and int(raw_date[1])<=12 and int(raw_date[0])<=31):

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


					with sql.connect("bot.sql") as con:
						cur = con.cursor()
						val = "'"+str(message.chat.id)+"','"+guest_name+"','"+phone+"','"+date_of_birth_str+"','"+str(promo_id)+"'"
						cur.execute("INSERT INTO users (chat_id, name, phone, bdate, promo_id) VALUES ("+val+")")
						cur.execute("SELECT last_insert_rowid()")
						cur_id = cur.fetchall()
						cur.execute("INSERT INTO promo_users (promo_id , user_id ) VALUES ('"+str(promo_id)+"','"+str(cur_id[0][0])+"')")

					#отправляем уведомление о регистрации сотрудникам
					call_promo("По вашей ссылке зарегестрирован гость " , cur_id[0][0])
					call_admins("Зарегестрирован гость " , cur_id[0][0])

					#после добавления БД оставить в QR коде только ссылку на бота с доб инфой его id в таблице
					qr_data = f"https://t.me/MiamiRegBot?start=x"+str(cur_id[0][0])
					qr = qrcode.make(qr_data)
					qr.save('qr_code.png')  # Сохраняем QR-код как изображение
					with open('qr_code.png', 'rb') as qr_file:
						bot.send_photo(message.chat.id, photo=qr_file)

			except:
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



def who_just_came(message,guest_id):
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

def register_admin(message):
	with sql.connect("bot.sql") as con:
		cur = con.cursor()
		cur.execute("INSERT INTO main_promo (chat_id) VALUES ('"+str(message.chat.id)+"');")
	bot.send_message(message.chat.id, "Вы были зарегестрированы как Генеральный промоутер\nВам будут приходить уведомления обо всех событиях гостей и промоутеров, а так же вам доступна команда /статистика")

def register_promo(message):
	name = message.text
	with sql.connect("bot.sql") as con:
		cur = con.cursor()
		cur.execute("INSERT INTO promo (chat_id , name) VALUES ('"+str(message.chat.id)+"','" +name+"');")

		cur.execute("SELECT last_insert_rowid()")
		cur_id = cur.fetchall()
	cur_id = cur_id[0][0]

	bot.send_message(message.chat.id, "Вы были зарегестрированы как промоутер\nВаша персональная ссылка для приглашения: https://t.me/MiamiRegBot?start="+str(cur_id)+" и QR-код для этой ссылки:")

	qr_data = f"https://t.me/MiamiRegBot?start="+str(cur_id)
	qr = qrcode.make(qr_data)
	qr.save('qr_code_invite.png')  # Сохраняем QR-код как изображение
	with open('qr_code_invite.png', 'rb') as qr_file:
		bot.send_photo(message.chat.id, photo=qr_file)





bot.polling(non_stop = True)