import asyncio
import os
import random
import sqlite3
import sys
import time
from aiogram import Bot, Dispatcher, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

# Токен берется из настроек сервера (Environment Variables)
API_TOKEN = os.getenv('BOT_TOKEN')

if not API_TOKEN:
  sys.exit('Ошибка: Токен бота не найден в переменных окружения (BOT_TOKEN)!')

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Инициализация базы данных
conn = sqlite3.connect('mini_games.db', check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''
               CREATE TABLE IF NOT EXISTS users
               (
                   user_id INTEGER PRIMARY KEY,
                   username TEXT,
                   balance INTEGER DEFAULT 100,
                   chulki_until INTEGER DEFAULT 0
               )
               ''')
conn.commit()

# Авто-добавление колонок при обновлении структуры базы
try:
  cursor.execute('ALTER TABLE users ADD COLUMN chulki_until INTEGER DEFAULT 0')
  conn.commit()
except sqlite3.OperationalError:
  pass

try:
  cursor.execute('ALTER TABLE users ADD COLUMN username TEXT')
  conn.commit()
except sqlite3.OperationalError:
  pass


def save_user(user_id: int, username: str = None):
  cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
  row = cursor.fetchone()
  if row is None:
    cursor.execute(
        'INSERT INTO users (user_id, username, balance, chulki_until) VALUES'
        ' (?, ?, 100, 0)',
        (user_id, username),
    )
  else:
    if username:
      cursor.execute(
          'UPDATE users SET username = ? WHERE user_id = ?', (username, user_id)
      )
  conn.commit()


def get_user_data(user_id: int):
  cursor.execute(
      'SELECT balance, chulki_until FROM users WHERE user_id = ?', (user_id,)
  )
  row = cursor.fetchone()
  if row is None:
    cursor.execute(
        'INSERT INTO users (user_id, balance, chulki_until) VALUES (?, 100, 0)',
        (user_id,),
    )
    conn.commit()
    return 100, 0
  return row[0], row[1]


def get_balance(user_id: int) -> int:
  return get_user_data(user_id)[0]


def update_balance(user_id: int, amount: int):
  cursor.execute(
      'UPDATE users SET balance = balance + ? WHERE user_id = ?',
      (amount, user_id),
  )
  conn.commit()


def is_chulki_active(user_id: int) -> bool:
  _, chulki_until = get_user_data(user_id)
  return time.time() < chulki_until


def set_chulki_boost(user_id: int, duration_seconds: int = 180):
  expire_time = int(time.time()) + duration_seconds
  cursor.execute(
      'UPDATE users SET chulki_until = ? WHERE user_id = ?',
      (expire_time, user_id),
  )
  conn.commit()


# --- MIDDLEWARE: Фиксирует пользователей ---
@dp.message.outer_middleware()
async def track_user_middleware(handler, event, data):
  if isinstance(event, Message) and event.from_user:
    save_user(event.from_user.id, event.from_user.username)
  return await handler(event, data)


GAMES = {
    'футбол': {'emoji': '⚽', 'title': '⚽️ Футбол'},
    'баскетбол': {'emoji': '🏀', 'title': '🏀 Баскетбол'},
    'слоты': {'emoji': '🎰', 'title': '🎰 Слоты'},
    'боулинг': {'emoji': '🎳', 'title': '🎳 Боулинг'},
    'дартс': {'emoji': '🎯', 'title': '🎯 Дартс'},
    'кубик': {'emoji': '🎲', 'title': '🎲 Кубик'},
}


def get_shop_keyboard(user_id: int) -> InlineKeyboardMarkup:
  active = is_chulki_active(user_id)
  btn_text = (
      '🧦 Купить чулки (50 кристаллов)'
      if not active
      else '🧦 Чулки уже активны (3 мин)'
  )
  return InlineKeyboardMarkup(
      inline_keyboard=[
          [InlineKeyboardButton(text=btn_text, callback_data='buy_chulki')],
          [InlineKeyboardButton(text='⬅️ Назад', callback_data='back_to_main')],
      ]
  )


def get_back_keyboard() -> InlineKeyboardMarkup:
  return InlineKeyboardMarkup(
      inline_keyboard=[
          [InlineKeyboardButton(text='⬅️ Назад', callback_data='back_to_main')]
      ]
  )


def get_profile_text(user_id: int) -> str:
  chulki_status = '✅' if is_chulki_active(user_id) else '❌'
  return (
      'Твой Профиль 👀\n\n'
      '⛏ Кирка: \n'
      '🌟 Прочность \n'
      '⛰️ Шахта: -\n'
      '🔬 Бур: -\n'
      '🔷 Топливо -\n'
      '🌟 Прочность -\n'
      '🏵 Сфера: -\n\n'
      '📊 Статистика:\n'
      ' 🪨 Походов: -\n'
      ' ⛏ Руд добыто: -\n'
      ' ✨ Кладов найдено: \n'
      ' 💎 Изумрудов: \n'
      ' 🗝️ Ключей: \n'
      f' 👑 Чулки: {chulki_status}\n'
      ' 🎒 Артефактов: \n'
      ' 📖 Коллекция: \n'
      ' 📅 Дней подряд (/daily): \n\n'
      '🎁 Кейсы:\n\n\n'
      '⚡ Глоб. буст к рудам: нет'
  )


# --- ОБРАБОТЧИКИ СООБЩЕНИЙ ---
@dp.message(F.text.contains('@MinePackBot_bot'))
async def minepack_bot_handler(message: Message):
  if random.randint(1, 100) <= 68:
    try:
      await message.reply('ТЕСТ')
    except Exception:
      await message.answer('ТЕСТ')


@dp.message(Command('start'))
async def start_cmd(message: Message):
  text = (
      '⛏️ фембой— команды (страница 1)\n\n'
      '👌 Чтобы начать добычу:\n\n'
      '⛏️ Команды:\n'
      '💰 /mh — казино\n'
      '📈 /shop — магазин\n'
      '👤 /Fprofile — профиль\n'
      '🚪 /fplay — подземелье\n'
      '🎁 /Fcase — кейсы'
  )
  await message.answer(text)


@dp.message(Command('Fprofile', 'fprofile', ignore_case=True))
async def profile_cmd(message: Message):
  user_id = message.from_user.id
  text = get_profile_text(user_id)
  await message.answer(text, reply_markup=get_back_keyboard())


@dp.message(Command('shop'))
async def shop_cmd(message: Message):
  user_id = message.from_user.id
  balance = get_balance(user_id)
  active = is_chulki_active(user_id)
  status = '🔥 (АКТИВНО)' if active else ''

  text = (
      '📈 **Магазин предметов**\n\n'
      f'👛 Твой баланс: {balance} 💎\n\n'
      f'🧦 **Чулки** {status}\n'
      '• Дает множитель ×3.0 вместо стандартного в играх\n'
      '• Время действия: 3 минуты\n'
      '• Цена: 50 💎'
  )
  await message.answer(
      text, reply_markup=get_shop_keyboard(user_id), parse_mode='Markdown'
  )


@dp.callback_query(F.data == 'buy_chulki')
async def buy_chulki_cb(callback: CallbackQuery):
  user_id = callback.from_user.id
  balance = get_balance(user_id)

  if is_chulki_active(user_id):
    await callback.answer('⚠️ Чулки уже активны!', show_alert=True)
    return

  if balance < 50:
    await callback.answer(
        '❌ Недостаточно кристаллов! Нужно 50 💎', show_alert=True
    )
    return

  update_balance(user_id, -50)
  set_chulki_boost(user_id, 180)

  new_balance = get_balance(user_id)
  await callback.answer(
      '🎉 Вы успешно купили чулки на 3 минуты!', show_alert=True
  )

  text = (
      '📈 **Магазин предметов**\n\n'
      f'👛 Твой баланс: {new_balance} 💎\n\n'
      '🧦 **Чулки** 🔥 (АКТИВНО)\n'
      '• Дает множитель ×3.0 вместо стандартного в играх\n'
      '• Время действия: 3 минуты\n'
      '• Цена: 50 💎'
  )
  await callback.message.edit_text(
      text, reply_markup=get_shop_keyboard(user_id), parse_mode='Markdown'
  )


@dp.callback_query(F.data == 'back_to_main')
async def back_to_main_cb(callback: CallbackQuery):
  main_text = (
      '⛏️ фембой— команды (страница 1)\n\n'
      '👌 Чтобы начать добычу:\n\n'
      '⛏️ Команды:\n'
      '💰 /mh — казино\n'
      '📈 /shop — магазин\n'
      '👤 /Fprofile — профиль\n'
      '🚪 /fplay — подземелье\n'
      '🎁 /Fcase — кейсы'
  )
  await callback.message.edit_text(main_text)
  await callback.answer()


@dp.message(Command('balance'))
async def balance_cmd(message: Message):
  balance = get_balance(message.from_user.id)
  await message.answer(f'👛 Баланс: **{balance} 💎**', parse_mode='Markdown')


@dp.message(Command('mh'))
async def play_game(message: Message):
  args = message.text.split()[1:]

  if len(args) < 2:
    await message.answer(
        '⚠️ Использование: `/mh <игра> <ставка>`\nПример: `/mh футбол 5`',
        parse_mode='Markdown',
    )
    return

  game_name = args[0].lower()
  if game_name not in GAMES:
    await message.answer(
        f"❌ Неизвестная игра. Доступные: {', '.join(GAMES.keys())}"
    )
    return

  try:
    bet = int(args[1])
  except ValueError:
    await message.answer('❌ Ставка должна быть целым числом.')
    return

  if bet < 5:
    await message.answer('⚠️ Минимальная ставка: **5 💎**', parse_mode='Markdown')
    return

  user_id = message.from_user.id
  balance = get_balance(user_id)

  if bet > balance:
    await message.answer(
        f'❌ Недостаточно кристаллов! Баланс: **{balance} 💎**',
        parse_mode='Markdown',
    )
    return

  update_balance(user_id, -bet)

  game_info = GAMES[game_name]
  dice_msg = await message.answer_dice(emoji=game_info['emoji'])
  val = dice_msg.dice.value

  await asyncio.sleep(3.5)

  win = False
  multiplier = 0.0
  win_text = ''
  loss_text = '💨 Удар мимо ворот!'

  if game_name == 'футбол':
    if val >= 3:
      win = True
      multiplier = 2.5
      win_text = '⚽️ ГОЛ! В девятку! Шедевр!'
    else:
      loss_text = '💨 Удар мимо ворот!'

  elif game_name == 'баскетбол':
    if val >= 4:
      win = True
      multiplier = 2.0
      win_text = '🏀 ТОЧНО В КОРЗИНУ! Чистый мяч!'
    else:
      loss_text = '💨 Мяч отскочил от дужки!'

  elif game_name == 'слоты':
    if val == 64:
      win = True
      multiplier = 10.0
      win_text = '🎰 ДЖЕКПОТ! Три семерки!'
    elif val in (1, 22, 43):
      win = True
      multiplier = 3.0
      win_text = '🎰 Выигрышная комбинация!'
    else:
      loss_text = '💨 Комбинация не сыграла!'

  elif game_name == 'боулинг':
    if val == 6:
      win = True
      multiplier = 3.0
      win_text = '🎳 СТРАЙК! Все кегли сбиты!'
    elif val >= 4:
      win = True
      multiplier = 1.5
      win_text = '🎳 Отличный бросок!'
    else:
      loss_text = '💨 Шар ушел в желоб!'

  elif game_name == 'дартс':
    if val == 6:
      win = True
      multiplier = 3.0
      win_text = '🎯 В САМОЕ ЯБЛОЧКО!'
    elif val >= 4:
      win = True
      multiplier = 1.5
      win_text = '🎯 Хорошее попадание!'
    else:
      loss_text = '💨 Промах мимо мишени!'

  elif game_name == 'кубик':
    if val >= 4:
      win = True
      multiplier = 2.0
      win_text = '🎲 Выпало выигрышное число!'
    else:
      loss_text = '💨 Неповезло!'

  chulki_active = is_chulki_active(user_id)
  if win and chulki_active:
    multiplier = 3.0

  if win:
    payout = int(bet * multiplier)
    profit = payout - bet
    update_balance(user_id, payout)
    current_balance = get_balance(user_id)

    mult_str = f'×{multiplier}' + (' (🧦 Буст)' if chulki_active else '')

    response = (
        f"{game_info['title']}\n\n"
        f'{win_text}\n\n'
        f'💰 Ставка: {bet} 💎\n'
        f'📈 Множитель: {mult_str}\n'
        f'✅ Выигрыш: +{profit} 💎\n\n'
        f'👛 Баланс: {current_balance} 💎'
    )
  else:
    current_balance = get_balance(user_id)

    response = (
        f"{game_info['title']}\n\n"
        f'{loss_text}\n\n'
        f'💰 Ставка: {bet} 💎\n'
        f'📈 Множитель: ×0.0\n'
        f'❌ Проигрыш: -{bet} 💎\n\n'
        f'👛 Баланс: {current_balance} 💎'
    )

  try:
    await message.reply(response)
  except TelegramBadRequest:
    await message.answer(response)


async def main():
  print('Запуск бота...')
  await dp.start_polling(bot)


if __name__ == '__main__':
  asyncio.run(main())
