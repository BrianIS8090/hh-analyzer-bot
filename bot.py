import asyncio
import logging
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN, ADMIN_USER_ID
from hh_api import get_all_vacancies, get_area_id
from analytics import analyze_vacancies, format_stats_report
from pdf_generator import generate_pdf_report
import pandas as pd

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Проверка токена
if not BOT_TOKEN:
    raise ValueError("Установите переменную окружения HH_BOT_TOKEN с токеном бота")

# Инициализация бота
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Состояния для FSM
class AnalyzeState(StatesGroup):
    waiting_for_query = State()
    waiting_for_city = State()

# Хранилище результатов
results_cache = {}

# Клавиатуры
def get_main_keyboard():
    kb = [
        [KeyboardButton(text="🔍 Анализировать вакансии")],
        [KeyboardButton(text="📄 Сохранить в PDF"), KeyboardButton(text="❓ Помощь")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, one_time_keyboard=False)


def get_cities_keyboard():
    kb = [
        [KeyboardButton(text="Москва"), KeyboardButton(text="Санкт-Петербург")],
        [KeyboardButton(text="Удалённо"), KeyboardButton(text="Все города")],
        [KeyboardButton(text="❌ Отмена")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, one_time_keyboard=True)


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 Привет! Я бот для анализа рынка вакансий с hh.ru\n\n"
        "Что я умею:\n"
        "• Искать вакансии по названию и городу\n"
        "• Строить статистику по зарплатам\n"
        "• Показывать топ работодателей\n"
        "• Извлекать популярные навыки\n\n"
        "Нажми <b>🔍 Анализировать вакансии</b> чтобы начать!",
        parse_mode="HTML",
        reply_markup=get_main_keyboard()
    )


@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer(
        "📖 <b>Как пользоваться ботом:</b>\n\n"
        "1. Нажми <b>🔍 Анализировать вакансии</b>\n"
        "2. Введи название вакансии (например: Python разработчик)\n"
        "3. Выбери город или укажи свой\n"
        "4. Жди отчёт (занимает 10-30 секунд)\n\n"
        "💡 <b>Примеры запросов:</b>\n"
        "• Python разработчик\n"
        "• Frontend разработчик React\n"
        "• DevOps инженер\n"
        "• Data Scientist\n"
        "• Product Manager\n\n"
        "📊 Отчёт включает:\n"
        "• Статистику зарплат (мин/макс/средняя/медиана)\n"
        "• Распределение по интервалам\n"
        "• Топ работодателей\n"
        "• Требования по опыту\n"
        "• Популярные навыки",
        parse_mode="HTML"
    )


@dp.message(F.text == "❓ Помощь")
async def btn_help(message: types.Message):
    await cmd_help(message)


@dp.message(F.text == "🔍 Анализировать вакансии")
async def btn_analyze(message: types.Message, state: FSMContext):
    await message.answer(
        "Введите название вакансии для анализа:\n\n"
        "Примеры:\n"
        "• Python разработчик\n"
        "• React разработчик\n"
        "• DevOps инженер"
    )
    await state.set_state(AnalyzeState.waiting_for_query)


@dp.message(AnalyzeState.waiting_for_query)
async def process_query(message: types.Message, state: FSMContext):
    query = message.text.strip()
    
    if len(query) < 3:
        await message.answer("Запрос слишком короткий. Введите минимум 3 символа.")
        return
    
    await state.update_data(query=query)
    await message.answer(
        "Выберите город или введите название:",
        reply_markup=get_cities_keyboard()
    )
    await state.set_state(AnalyzeState.waiting_for_city)


@dp.message(AnalyzeState.waiting_for_city)
async def process_city(message: types.Message, state: FSMContext):
    text = message.text.strip()
    
    if text == "❌ Отмена":
        await state.clear()
        await message.answer("Отменено", reply_markup=get_main_keyboard())
        return
    
    data = await state.get_data()
    query = data["query"]
    
    # Определяем город
    if text == "Все города":
        area = None
        area_name = "Все города"
    elif text in ["Москва", "Санкт-Петербург", "Удалённо"]:
        area = text
        area_name = text
    else:
        area = text
        area_name = text
    
    await state.clear()
    
    # Отправляем сообщение о начале анализа
    status_msg = await message.answer(
        f"🔍 Анализирую вакансии...\n\n"
        f"Запрос: {query}\n"
        f"Город: {area_name or 'Все города'}\n\n"
        f"Это займёт 10-30 секунд..."
    )
    
    try:
        # Получаем вакансии
        vacancies = await get_all_vacancies(
            text=query,
            area=area,
            max_pages=10  # До 1000 вакансий
        )
        
        if not vacancies:
            await status_msg.delete()
            await message.answer(
                "❌ Вакансии не найдены. Попробуйте изменить запрос.",
                reply_markup=get_main_keyboard()
            )
            return
        
        # Анализируем
        stats = analyze_vacancies(vacancies)
        
        # Формируем отчёт
        report = format_stats_report(stats, query, area_name)
        
        # Сохраняем в кеш
        user_id = message.from_user.id
        results_cache[user_id] = {
            "query": query,
            "area": area_name,
            "stats": stats,
            "vacancies": vacancies,  # Сохраняем вакансии для PDF
            "vacancies_count": len(vacancies)
        }
        
        await status_msg.delete()
        await message.answer(report, parse_mode="HTML", reply_markup=get_main_keyboard())
        
    except Exception as e:
        logger.error(f"Error analyzing vacancies: {e}")
        await status_msg.delete()
        await message.answer(
            f"❌ Ошибка при анализе: {str(e)}",
            reply_markup=get_main_keyboard()
        )


@dp.message(F.text == "📄 Сохранить в PDF")
async def btn_pdf(message: types.Message):
    user_id = message.from_user.id
    
    if user_id not in results_cache:
        await message.answer(
            "❌ Нет данных для сохранения.\n"
            "Сначала выполните анализ вакансий.",
            reply_markup=get_main_keyboard()
        )
        return
    
    cache = results_cache[user_id]
    
    status_msg = await message.answer("📄 Генерирую PDF отчёт...")
    
    try:
        pdf_buf = generate_pdf_report(
            query=cache["query"],
            area=cache["area"],
            stats=cache["stats"],
            vacancies=cache["vacancies"]
        )
        
        # Отправляем PDF
        from aiogram.types import BufferedInputFile
        pdf_file = BufferedInputFile(
            file=pdf_buf.read(),
            filename=f"vacancies_{cache['query']}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
        )
        
        await status_msg.delete()
        await message.answer_document(
            document=pdf_file,
            caption=f"📊 PDF отчёт: {cache['query']}\n📍 {cache['area'] or 'Все города'}\n📋 {cache['vacancies_count']} вакансий",
            reply_markup=get_main_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Error generating PDF: {e}")
        await status_msg.edit_text(
            f"❌ Ошибка при генерации PDF: {str(e)}",
            reply_markup=None
        )


@dp.message(F.text == "📊 Моя статистика")
async def btn_stats(message: types.Message):
    user_id = message.from_user.id
    
    if user_id not in results_cache:
        await message.answer(
            "У вас пока нет сохранённых результатов.\n"
            "Сначала выполните анализ вакансий.",
            reply_markup=get_main_keyboard()
        )
        return
    
    cache = results_cache[user_id]
    report = format_stats_report(cache["stats"], cache["query"], cache["area"])
    await message.answer(report, parse_mode="HTML")


@dp.message()
async def unknown_message(message: types.Message):
    await message.answer(
        "Я не понял команду. Используйте кнопки меню.",
        reply_markup=get_main_keyboard()
    )


async def main():
    logger.info("Starting HH Analytics Bot...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
