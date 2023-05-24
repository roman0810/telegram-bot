import telebot
import datetime
import qrcode

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
	else:
		print("-->> неверный айди промоутера ", raw_promo_id)

	#при битой ссылке гостя получит мнимый промоутер
	bot.send_message(message.chat.id, "Добро пожаловать в бот Майами Клуб!\nДавайте пройдем небольшую регистрацию - напишите свое имя.")
	bot.register_next_step_handler(message,get_name)

def get_name(message):
	global guest_name
	guest_name = message.text


	markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
	markup.add(telebot.types.KeyboardButton(text='Отправить номер телефона', request_contact=True))
	bot.send_message(message.chat.id, "Теперь отправьте мне свой номер телефона с помощью кнопки ниже.", reply_markup=markup)

	bot.register_next_step_handler(message, get_phone)

def get_phone(message):
	global phone
	phone = message.contact.phone_number


	bot.send_message(message.chat.id, "введите свою дату рождения в формате дд.мм.гггг")
	bot.register_next_step_handler(message, get_date)

def get_date(message):
	global guest_name , phone , date
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

					#отправляем уведомление о регистрации сотрудникам
					call_admins_reg()
					call_promo_reg()

					qr_data = f"Имя: {guest_name}\nТелефон: {phone}\nДата рождения: {date_of_birth_str}\nНомер промоутера: {str(promo_id)}"
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
call_promo_reg():
	return

call_admins_reg():
	return




bot.polling(non_stop = True)